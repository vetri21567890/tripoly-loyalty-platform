from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models.earning_rules import BookingBonusBracket, ReferralRewardRule
from app.models.enums import ExpiryType, MissionStatus
from app.models.mission import CustomerMissionCompletion, Mission, MissionRewardRule
from app.models.ugc import UgcRewardRule
from app.services.tier_service import TierService
from app.services.wallet_service import WalletService


class EarningService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet = WalletService(db)
        self.tier = TierService(db)

    async def _get_mission_rule_coins(self, mission_code: str) -> int:
        result = await self.db.execute(select(Mission).where(Mission.code == mission_code))
        mission = result.scalar_one_or_none()
        if not mission:
            return 0
        rule_result = await self.db.execute(
            select(MissionRewardRule)
            .where(MissionRewardRule.mission_id == mission.id, MissionRewardRule.status == "active")
            .order_by(MissionRewardRule.effective_from.desc())
            .limit(1)
        )
        rule = rule_result.scalar_one_or_none()
        return rule.coins_awarded if rule else 0

    async def issue_complete_profile_bonus(self, customer_id: UUID) -> tuple[int, UUID | None]:
        mission_result = await self.db.execute(select(Mission).where(Mission.code == "COMPLETE_PROFILE"))
        mission = mission_result.scalar_one_or_none()
        if not mission:
            return 0, None

        existing = await self.db.execute(
            select(CustomerMissionCompletion).where(
                CustomerMissionCompletion.customer_id == customer_id,
                CustomerMissionCompletion.mission_id == mission.id,
                CustomerMissionCompletion.status == MissionStatus.COMPLETED,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Profile mission already completed")

        coins = await self._get_mission_rule_coins("COMPLETE_PROFILE") or 50
        _, grant = await self.wallet.issue_coins(
            customer_id=customer_id,
            amount=coins,
            grant_source="COMPLETE_PROFILE",
            reason_code="COMPLETE_PROFILE",
            idempotency_key=f"mission:COMPLETE_PROFILE:{customer_id}",
            reference_type="mission",
            reference_id=mission.id,
        )

        completion = CustomerMissionCompletion(
            customer_id=customer_id,
            mission_id=mission.id,
            status=MissionStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            approved_at=datetime.now(timezone.utc),
            coins_awarded=coins,
            coin_grant_id=grant.id,
        )
        self.db.add(completion)
        balance = await self.wallet.ensure_wallet_balance(customer_id)
        await self.tier.evaluate_and_upgrade(customer_id, balance.lifetime_coins_earned, "COMPLETE_PROFILE")
        return coins, grant.id

    async def issue_booking_bonus(self, customer_id: UUID, booking_event_id: UUID, amount_inr: Decimal) -> int:
        now = datetime.now(timezone.utc)
        bracket_result = await self.db.execute(
            select(BookingBonusBracket).where(
                BookingBonusBracket.status == "active",
                BookingBonusBracket.min_amount_inr <= amount_inr,
                or_(
                    BookingBonusBracket.max_amount_inr.is_(None),
                    BookingBonusBracket.max_amount_inr >= amount_inr,
                ),
                or_(BookingBonusBracket.effective_to.is_(None), BookingBonusBracket.effective_to >= now),
                BookingBonusBracket.effective_from <= now,
            ).order_by(BookingBonusBracket.min_amount_inr.desc()).limit(1)
        )
        bracket = bracket_result.scalar_one_or_none()
        if not bracket:
            return 0

        coins = bracket.coins_awarded
        await self.wallet.issue_coins(
            customer_id=customer_id,
            amount=coins,
            grant_source="BOOKING_BONUS",
            reason_code=f"BOOKING_BONUS_{bracket.id}",
            idempotency_key=f"booking:{booking_event_id}",
            earned_date=date.today(),
            reference_type="booking_event",
            reference_id=booking_event_id,
            booking_event_id=booking_event_id,
        )
        balance = await self.wallet.ensure_wallet_balance(customer_id)
        await self.tier.evaluate_and_upgrade(customer_id, balance.lifetime_coins_earned, "BOOKING_BONUS")
        return coins

    async def issue_referral_reward(
        self, referrer_customer_id: UUID, attribution_id: UUID, booking_event_id: UUID
    ):
        now = datetime.now(timezone.utc)
        rule_result = await self.db.execute(
            select(ReferralRewardRule).where(
                ReferralRewardRule.status == "active",
                or_(ReferralRewardRule.effective_to.is_(None), ReferralRewardRule.effective_to >= now),
            ).order_by(ReferralRewardRule.effective_from.desc()).limit(1)
        )
        rule = rule_result.scalar_one_or_none()
        coins = rule.qualified_coins if rule else 500

        return await self.wallet.issue_coins(
            customer_id=referrer_customer_id,
            amount=coins,
            grant_source="REFERRAL_REWARD",
            reason_code="REFERRAL_QUALIFIED",
            idempotency_key=f"referral:{attribution_id}:{booking_event_id}",
            reference_type="referral_attribution",
            reference_id=attribution_id,
            referral_attribution_id=attribution_id,
            booking_event_id=booking_event_id,
        )

    async def issue_ugc_reward(self, customer_id: UUID, ugc_attempt_id: UUID, ugc_type: str) -> int:
        from app.models.enums import UgcType

        ut = UgcType(ugc_type)
        rule_result = await self.db.execute(
            select(UgcRewardRule).where(UgcRewardRule.ugc_type == ut, UgcRewardRule.status == "active")
        )
        rule = rule_result.scalar_one_or_none()
        if not rule:
            defaults = {
                UgcType.PHOTO: 50,
                UgcType.REVIEW_SCREENSHOT: 100,
                UgcType.TESTIMONIAL: 150,
                UgcType.VIDEO: 200,
                UgcType.REEL: 250,
            }
            coins = defaults.get(ut, 0)
        else:
            coins = rule.coins_awarded

        if coins <= 0:
            return 0

        _, grant = await self.wallet.issue_coins(
            customer_id=customer_id,
            amount=coins,
            grant_source="UGC_APPROVED",
            reason_code=f"UGC_{ut.value.upper()}",
            idempotency_key=f"ugc:{ugc_attempt_id}",
            reference_type="ugc_attempt",
            reference_id=ugc_attempt_id,
            ugc_attempt_id=ugc_attempt_id,
        )
        balance = await self.wallet.ensure_wallet_balance(customer_id)
        await self.tier.evaluate_and_upgrade(customer_id, balance.lifetime_coins_earned, "UGC_APPROVED")
        return coins
