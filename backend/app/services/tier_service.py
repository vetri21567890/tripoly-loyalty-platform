from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import LoyaltyTierCode
from app.models.notification import InAppNotification
from app.models.tier import CustomerCurrentTier, CustomerTierHistory, LoyaltyTier


class TierService:
    TIER_THRESHOLDS = [
        (LoyaltyTierCode.EXPLORER, 0, 999),
        (LoyaltyTierCode.VOYAGER, 1000, 2999),
        (LoyaltyTierCode.ELITE_TRAVELLER, 3000, 9999),
        (LoyaltyTierCode.GLOBAL_NOMAD, 10000, None),
    ]

    def __init__(self, db: AsyncSession):
        self.db = db

    def tier_for_lifetime(self, lifetime: int) -> LoyaltyTierCode:
        if lifetime >= 10000:
            return LoyaltyTierCode.GLOBAL_NOMAD
        if lifetime >= 3000:
            return LoyaltyTierCode.ELITE_TRAVELLER
        if lifetime >= 1000:
            return LoyaltyTierCode.VOYAGER
        return LoyaltyTierCode.EXPLORER

    async def get_tier_by_code(self, code: LoyaltyTierCode) -> LoyaltyTier | None:
        result = await self.db.execute(select(LoyaltyTier).where(LoyaltyTier.code == code))
        return result.scalar_one_or_none()

    async def tier_for_lifetime_from_db(self, lifetime: int) -> LoyaltyTier | None:
        result = await self.db.execute(
            select(LoyaltyTier)
            .where(
                LoyaltyTier.status == "active",
                LoyaltyTier.min_lifetime_coins <= lifetime,
                (LoyaltyTier.max_lifetime_coins.is_(None)) | (LoyaltyTier.max_lifetime_coins >= lifetime),
            )
            .order_by(LoyaltyTier.sort_order)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def evaluate_and_upgrade(self, customer_id: UUID, lifetime_coins: int, source: str) -> bool:
        target_tier = await self.tier_for_lifetime_from_db(lifetime_coins)
        if not target_tier:
            return False
        target_code = target_tier.code
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(CustomerCurrentTier).where(CustomerCurrentTier.customer_id == customer_id)
        )
        current = result.scalar_one_or_none()

        if current and current.tier_id == target_tier.id:
            return False

        if current:
            current.tier_id = target_tier.id
            current.lifetime_coins_at_set = lifetime_coins
            current.set_at = now
        else:
            self.db.add(
                CustomerCurrentTier(
                    customer_id=customer_id,
                    tier_id=target_tier.id,
                    lifetime_coins_at_set=lifetime_coins,
                    set_at=now,
                )
            )

        self.db.add(
            CustomerTierHistory(
                customer_id=customer_id,
                tier_id=target_tier.id,
                lifetime_coins_at_upgrade=lifetime_coins,
                source=source,
                achieved_at=now,
            )
        )

        self.db.add(
            InAppNotification(
                customer_id=customer_id,
                type="TIER_UPGRADE",
                title="Tier upgraded!",
                body=f"Congratulations! You are now {target_tier.name}.",
                metadata_jsonb={"tier_code": target_code.value, "lifetime_coins": lifetime_coins},
            )
        )
        await self.db.flush()
        return True
