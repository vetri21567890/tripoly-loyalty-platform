from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, RewardUnavailableError
from app.models.enums import RewardStatus
from app.models.notification import InAppNotification
from app.models.rewards import RewardCatalog, RewardRedemption
from app.services.program_settings_service import ProgramSettingsService
from app.services.wallet_service import WalletService


class RewardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet = WalletService(db)
        self.program_settings = ProgramSettingsService(db)

    async def redeem(
        self, customer_id: UUID, reward_catalog_id: UUID, idempotency_key: str
    ) -> RewardRedemption:
        existing = await self.db.execute(
            select(RewardRedemption).where(
                RewardRedemption.customer_id == customer_id,
                RewardRedemption.idempotency_key == idempotency_key,
            )
        )
        redemption = existing.scalar_one_or_none()
        if redemption:
            return redemption

        result = await self.db.execute(
            select(RewardCatalog)
            .where(RewardCatalog.id == reward_catalog_id, RewardCatalog.deleted_at.is_(None))
            .with_for_update()
        )
        reward = result.scalar_one_or_none()
        if not reward or reward.status != "active":
            raise NotFoundError("Reward not found")

        balance = await self.wallet.ensure_wallet_balance(customer_id)
        minimum_redemption = await self.program_settings.get("minimum_redemption_coins", 500)
        if reward.cost_coins < int(minimum_redemption):
            raise ConflictError(f"Minimum redemption is {minimum_redemption} Travel Coins")
        if balance.available_coins < reward.cost_coins:
            from app.core.exceptions import InsufficientCoinsError

            raise InsufficientCoinsError()

        if not reward.unlimited_inventory:
            if reward.inventory_remaining is None or reward.inventory_remaining <= 0:
                raise RewardUnavailableError()
            reward.inventory_remaining -= 1
            if reward.inventory_remaining == 0:
                reward.status = "inactive"

        voucher_code = f"TRIP-{uuid4().hex[:10].upper()}"

        redemption = RewardRedemption(
            customer_id=customer_id,
            reward_catalog_id=reward.id,
            status=RewardStatus.COMPLETED,
            coins_spent=reward.cost_coins,
            idempotency_key=idempotency_key,
            redeemed_at=datetime.now(timezone.utc),
            metadata_jsonb={"voucher_code": voucher_code},
        )
        self.db.add(redemption)
        await self.db.flush()

        await self.wallet.redeem_coins(
            customer_id=customer_id,
            amount=reward.cost_coins,
            idempotency_key=f"redeem:{idempotency_key}",
            reason_code="REDEEM_VOUCHER",
            reward_redemption_id=redemption.id,
        )

        self.db.add(
            InAppNotification(
                customer_id=customer_id,
                type="REWARD_REDEMPTION",
                title="Reward redeemed",
                body=f"You redeemed {reward.title} for {reward.cost_coins} Tripoly Coins.",
                metadata_jsonb={"reward_catalog_id": str(reward.id), "redemption_id": str(redemption.id)},
            )
        )
        await self.db.flush()
        return redemption
