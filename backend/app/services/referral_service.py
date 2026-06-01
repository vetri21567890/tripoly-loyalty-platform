import hashlib
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ValidationError
from app.models.customer import Customer, CustomerDevice
from app.models.enums import ReferralStatus
from app.models.referral import ReferralAttribution, ReferralCode, ReferralStatusHistory
from app.services.earning_service import EarningService


class ReferralService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_code(self, customer_id: UUID) -> ReferralCode:
        result = await self.db.execute(
            select(ReferralCode).where(ReferralCode.customer_id == customer_id, ReferralCode.status == "active")
        )
        code = result.scalar_one_or_none()
        if code:
            return code
        code = ReferralCode(customer_id=customer_id, code=f"TRIP{str(customer_id).replace('-', '')[:8].upper()}")
        self.db.add(code)
        await self.db.flush()
        return code

    def _link_hash(self, link: str | None) -> str | None:
        if not link:
            return None
        return hashlib.sha256(link.encode()).hexdigest()

    async def track_referral(
        self,
        referral_code: str,
        referral_source: str,
        referred_phone: str | None = None,
        referred_email: str | None = None,
        referral_link: str | None = None,
        device_fingerprint: str | None = None,
    ) -> ReferralAttribution:
        code_result = await self.db.execute(
            select(ReferralCode).where(ReferralCode.code == referral_code, ReferralCode.status == "active")
        )
        ref_code = code_result.scalar_one_or_none()
        if not ref_code:
            raise ValidationError("Invalid referral code")

        if referred_phone:
            cust = await self.db.execute(select(Customer).where(Customer.phone == referred_phone))
            referred = cust.scalar_one_or_none()
            if referred and referred.id == ref_code.customer_id:
                raise ConflictError("Cannot refer yourself", code="REFERRAL_SELF_REFERRAL")
        if referred_email:
            cust = await self.db.execute(select(Customer).where(Customer.email == referred_email))
            referred = cust.scalar_one_or_none()
            if referred and referred.id == ref_code.customer_id:
                raise ConflictError("Cannot refer yourself", code="REFERRAL_SELF_REFERRAL")

        attr = ReferralAttribution(
            referral_code_id=ref_code.id,
            referrer_customer_id=ref_code.customer_id,
            referred_phone=referred_phone,
            referred_email=referred_email,
            referral_link_hash=self._link_hash(referral_link),
            referral_source=referral_source,
            status=ReferralStatus.INVITED,
            invited_at=datetime.now(timezone.utc),
        )
        self.db.add(attr)
        await self.db.flush()
        self._add_history(attr.id, ReferralStatus.INVITED)
        return attr

    def _add_history(
        self,
        attribution_id: UUID,
        status: ReferralStatus,
        booking_event_id: UUID | None = None,
        coin_grant_id: UUID | None = None,
    ) -> None:
        self.db.add(
            ReferralStatusHistory(
                referral_attribution_id=attribution_id,
                status=status,
                changed_at=datetime.now(timezone.utc),
                booking_event_id=booking_event_id,
                coin_grant_id=coin_grant_id,
            )
        )

    async def on_customer_registered(self, customer_id: UUID, phone: str | None, email: str | None) -> None:
        q = select(ReferralAttribution).where(
            ReferralAttribution.status == ReferralStatus.INVITED,
            ReferralAttribution.referred_customer_id.is_(None),
        )
        if phone:
            q = q.where(ReferralAttribution.referred_phone == phone)
        elif email:
            q = q.where(ReferralAttribution.referred_email == email)
        else:
            return

        result = await self.db.execute(q)
        for attr in result.scalars().all():
            if attr.referrer_customer_id == customer_id:
                continue
            attr.referred_customer_id = customer_id
            attr.status = ReferralStatus.REGISTERED
            attr.registered_at = datetime.now(timezone.utc)
            self._add_history(attr.id, ReferralStatus.REGISTERED)

    async def on_profile_completed(self, customer_id: UUID) -> None:
        result = await self.db.execute(
            select(ReferralAttribution).where(
                ReferralAttribution.referred_customer_id == customer_id,
                ReferralAttribution.status == ReferralStatus.REGISTERED,
            )
        )
        for attr in result.scalars().all():
            attr.status = ReferralStatus.PROFILE_COMPLETED
            attr.profile_completed_at = datetime.now(timezone.utc)
            self._add_history(attr.id, ReferralStatus.PROFILE_COMPLETED)

    async def on_first_booking_confirmed(
        self, customer_id: UUID, booking_event_id: UUID
    ) -> None:
        result = await self.db.execute(
            select(ReferralAttribution).where(
                ReferralAttribution.referred_customer_id == customer_id,
                ReferralAttribution.status.in_(
                    [ReferralStatus.PROFILE_COMPLETED, ReferralStatus.REGISTERED]
                ),
            )
        )
        earning = EarningService(self.db)
        for attr in result.scalars().all():
            attr.status = ReferralStatus.BOOKING_CONFIRMED
            attr.booking_confirmed_at = datetime.now(timezone.utc)
            self._add_history(attr.id, ReferralStatus.BOOKING_CONFIRMED, booking_event_id=booking_event_id)

            attr.status = ReferralStatus.QUALIFIED
            attr.qualified_at = datetime.now(timezone.utc)
            self._add_history(attr.id, ReferralStatus.QUALIFIED, booking_event_id=booking_event_id)

            _, grant = await earning.issue_referral_reward(
                attr.referrer_customer_id, attr.id, booking_event_id
            )
            attr.status = ReferralStatus.REWARD_ISSUED
            attr.reward_issued_at = datetime.now(timezone.utc)
            self._add_history(
                attr.id, ReferralStatus.REWARD_ISSUED, booking_event_id=booking_event_id, coin_grant_id=grant.id
            )

    async def register_device(self, customer_id: UUID, device_fingerprint: str) -> None:
        existing = await self.db.execute(
            select(CustomerDevice).where(CustomerDevice.device_fingerprint == device_fingerprint)
        )
        devices = list(existing.scalars().all())
        if len(devices) >= 3 and not any(d.customer_id == customer_id for d in devices):
            raise ConflictError("Device already associated with multiple accounts", code="REFERRAL_DEVICE_ABUSE")

        if not any(d.customer_id == customer_id and d.device_fingerprint == device_fingerprint for d in devices):
            self.db.add(
                CustomerDevice(
                    customer_id=customer_id,
                    device_fingerprint=device_fingerprint,
                    last_seen_at=datetime.now(timezone.utc),
                )
            )
