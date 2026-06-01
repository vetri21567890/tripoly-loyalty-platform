"""Wallet ledger service: coin grants, FIFO redemption, expiry."""

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from dateutil.relativedelta import relativedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, InsufficientCoinsError
from app.models.enums import (
    CoinGrantStatus,
    CoinTransactionDirection,
    ExpiryType,
    WalletOperationType,
)
from app.models.wallet import CoinGrant, CoinTransaction, WalletBalance, WalletOperation
from app.services.program_settings_service import ProgramSettingsService


class WalletService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.program_settings = ProgramSettingsService(db)

    async def ensure_wallet_balance(self, customer_id: UUID) -> WalletBalance:
        result = await self.db.execute(
            select(WalletBalance).where(WalletBalance.customer_id == customer_id)
        )
        balance = result.scalar_one_or_none()
        if balance is None:
            balance = WalletBalance(customer_id=customer_id)
            self.db.add(balance)
            await self.db.flush()
        return balance

    def compute_expiry_date(
        self, earned_date: date, expiry_type: ExpiryType, override_months: int | None = None
    ) -> date | None:
        if expiry_type == ExpiryType.NO_EXPIRY:
            return None
        if expiry_type == ExpiryType.CAMPAIGN_OVERRIDE and override_months:
            return earned_date + relativedelta(months=override_months)
        return earned_date + relativedelta(months=self.settings.coin_standard_expiry_months)

    async def compute_expiry_date_async(
        self, earned_date: date, expiry_type: ExpiryType, override_months: int | None = None
    ) -> date | None:
        if expiry_type == ExpiryType.NO_EXPIRY:
            return None
        if expiry_type == ExpiryType.CAMPAIGN_OVERRIDE and override_months:
            return earned_date + relativedelta(months=override_months)
        months = await self.program_settings.get("coin_expiry_months", self.settings.coin_standard_expiry_months)
        return earned_date + relativedelta(months=int(months))

    async def issue_coins(
        self,
        customer_id: UUID,
        amount: int,
        grant_source: str,
        reason_code: str,
        idempotency_key: str,
        earned_date: date | None = None,
        expiry_type: ExpiryType = ExpiryType.STANDARD_24_MONTHS,
        expiry_override_months: int | None = None,
        reference_type: str | None = None,
        reference_id: UUID | None = None,
        campaign_id: UUID | None = None,
        ugc_attempt_id: UUID | None = None,
        booking_event_id: UUID | None = None,
        referral_attribution_id: UUID | None = None,
    ) -> tuple[WalletOperation, CoinGrant]:
        if amount <= 0:
            raise ConflictError("Amount must be positive")

        existing = await self.db.execute(
            select(WalletOperation).where(
                WalletOperation.customer_id == customer_id,
                WalletOperation.idempotency_key == idempotency_key,
            )
        )
        op = existing.scalar_one_or_none()
        if op:
            grant_result = await self.db.execute(
                select(CoinGrant).join(CoinTransaction).where(
                    CoinTransaction.wallet_operation_id == op.id
                ).limit(1)
            )
            grant = grant_result.scalar_one_or_none()
            if grant:
                return op, grant
            raise ConflictError("Idempotent operation exists without grant", code="CONFLICT")

        earned = earned_date or date.today()
        expiry_date = await self.compute_expiry_date_async(earned, expiry_type, expiry_override_months)

        status = CoinGrantStatus.ACTIVE
        amount_remaining = amount
        if expiry_date and expiry_date <= date.today():
            status = CoinGrantStatus.EXPIRED
            amount_remaining = 0

        operation = WalletOperation(
            customer_id=customer_id,
            operation_type=WalletOperationType.EARN,
            idempotency_key=idempotency_key,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        self.db.add(operation)
        await self.db.flush()

        grant = CoinGrant(
            customer_id=customer_id,
            grant_source=grant_source,
            reference_type=reference_type,
            reference_id=reference_id,
            amount_total=amount,
            amount_remaining=amount_remaining,
            earned_date=earned,
            expiry_type=expiry_type,
            expiry_date=expiry_date,
            status=status,
            amount_expired=amount if status == CoinGrantStatus.EXPIRED else 0,
            campaign_id=campaign_id,
            ugc_attempt_id=ugc_attempt_id,
            booking_event_id=booking_event_id,
            referral_attribution_id=referral_attribution_id,
        )
        self.db.add(grant)
        await self.db.flush()

        tx = CoinTransaction(
            wallet_operation_id=operation.id,
            customer_id=customer_id,
            coin_grant_id=grant.id,
            direction=CoinTransactionDirection.CREDIT,
            amount=amount,
            earned_date=earned,
            expiry_date=expiry_date,
            reason_code=reason_code,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        self.db.add(tx)

        balance = await self.ensure_wallet_balance(customer_id)
        balance.lifetime_coins_earned += amount
        balance.available_coins += amount_remaining
        if status == CoinGrantStatus.EXPIRED:
            balance.expired_coins += amount

        await self.db.flush()
        return operation, grant

    async def _select_fifo_grants(self, customer_id: UUID, amount_needed: int) -> list[tuple[CoinGrant, int]]:
        result = await self.db.execute(
            select(CoinGrant)
            .where(
                CoinGrant.customer_id == customer_id,
                CoinGrant.status == CoinGrantStatus.ACTIVE,
                CoinGrant.amount_remaining > 0,
            )
            .order_by(
                CoinGrant.expiry_date.is_(None).asc(),
                CoinGrant.expiry_date.asc(),
                CoinGrant.earned_date.asc(),
                CoinGrant.created_at.asc(),
            )
            .with_for_update()
        )
        grants = list(result.scalars().all())
        allocations: list[tuple[CoinGrant, int]] = []
        remaining = amount_needed
        for grant in grants:
            if remaining <= 0:
                break
            take = min(grant.amount_remaining, remaining)
            allocations.append((grant, take))
            remaining -= take
        if remaining > 0:
            raise InsufficientCoinsError()
        return allocations

    async def redeem_coins(
        self,
        customer_id: UUID,
        amount: int,
        idempotency_key: str,
        reason_code: str,
        reward_redemption_id: UUID,
    ) -> WalletOperation:
        existing = await self.db.execute(
            select(WalletOperation).where(
                WalletOperation.customer_id == customer_id,
                WalletOperation.idempotency_key == idempotency_key,
            )
        )
        existing_op = existing.scalar_one_or_none()
        if existing_op:
            return existing_op

        balance = await self.ensure_wallet_balance(customer_id)
        if balance.available_coins < amount:
            raise InsufficientCoinsError()

        operation = WalletOperation(
            customer_id=customer_id,
            operation_type=WalletOperationType.REDEEM,
            idempotency_key=idempotency_key,
            reference_type="reward_redemption",
            reference_id=reward_redemption_id,
        )
        self.db.add(operation)
        await self.db.flush()

        allocations = await self._select_fifo_grants(customer_id, amount)
        for grant, take in allocations:
            grant.amount_remaining -= take
            if grant.amount_remaining == 0:
                grant.status = CoinGrantStatus.FULLY_REDEEMED

            tx = CoinTransaction(
                wallet_operation_id=operation.id,
                customer_id=customer_id,
                coin_grant_id=grant.id,
                direction=CoinTransactionDirection.DEBIT,
                amount=take,
                earned_date=grant.earned_date,
                expiry_date=grant.expiry_date,
                reason_code=reason_code,
                reference_type="reward_redemption",
                reference_id=reward_redemption_id,
                reward_redemption_id=reward_redemption_id,
            )
            self.db.add(tx)

        balance.available_coins -= amount
        balance.redeemed_coins_to_date += amount
        await self.db.flush()
        return operation

    async def expire_due_grants(self, customer_id: UUID | None = None) -> int:
        """Expire grants past expiry_date. Returns count expired."""
        q = select(CoinGrant).where(
            CoinGrant.status == CoinGrantStatus.ACTIVE,
            CoinGrant.expiry_date.isnot(None),
            CoinGrant.expiry_date <= date.today(),
            CoinGrant.amount_remaining > 0,
        )
        if customer_id:
            q = q.where(CoinGrant.customer_id == customer_id)

        result = await self.db.execute(q.with_for_update())
        grants = list(result.scalars().all())
        count = 0
        for grant in grants:
            expired_amount = grant.amount_remaining
            grant.amount_expired = expired_amount
            grant.amount_remaining = 0
            grant.status = CoinGrantStatus.EXPIRED
            grant.expired_at = datetime.now(timezone.utc)

            balance = await self.ensure_wallet_balance(grant.customer_id)
            balance.available_coins -= expired_amount
            balance.expired_coins += expired_amount
            count += 1
        await self.db.flush()
        return count

    async def get_expiring_soon_grants(
        self, customer_id: UUID, within_days: int, limit: int = 20
    ) -> tuple[list[CoinGrant], int]:
        """
        Returns active, not-yet-expired coin grants expiring within `within_days`.
        `CoinGrant.expiry_date` is a DATE column, so comparisons are done on date boundaries.
        """
        today = date.today()
        end_date = today + timedelta(days=within_days)

        q = (
            select(CoinGrant)
            .where(
                CoinGrant.customer_id == customer_id,
                CoinGrant.status == CoinGrantStatus.ACTIVE,
                CoinGrant.expiry_date.isnot(None),
                CoinGrant.expiry_date > today,
                CoinGrant.expiry_date <= end_date,
                CoinGrant.amount_remaining > 0,
            )
            .order_by(CoinGrant.expiry_date.asc(), CoinGrant.earned_date.asc())
            .limit(limit)
        )
        result = await self.db.execute(q)
        grants = result.scalars().all()
        total = sum(g.amount_remaining for g in grants)
        return list(grants), total
