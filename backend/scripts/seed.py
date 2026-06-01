"""Seed database with tiers, missions, earning rules, admin user."""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.models.auth import AdminRole, AdminUser, AdminUserRole
from app.models.campaign import Campaign
from app.models.earning_rules import BookingBonusBracket, ReferralRewardRule
from app.models.enums import (
    CampaignEligibilityType,
    CampaignType,
    LoyaltyTierCode,
    UgcType,
)
from app.models.mission import Mission, MissionRewardRule
from app.models.rewards import RewardCatalog
from app.models.settings import LoyaltyProgramSetting
from app.models.tier import LoyaltyTier
from app.models.ugc import UgcRewardRule, UgcSubmissionLimit

settings = get_settings()
DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@tripoly.app")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


async def seed() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as db:
        tiers = [
            (LoyaltyTierCode.EXPLORER, "Explorer", 0, 999, 1),
            (LoyaltyTierCode.VOYAGER, "Voyager", 1000, 2999, 2),
            (LoyaltyTierCode.ELITE_TRAVELLER, "Elite Traveller", 3000, 9999, 3),
            (LoyaltyTierCode.GLOBAL_NOMAD, "Global Nomad", 10000, None, 4),
        ]
        for code, name, min_c, max_c, order in tiers:
            exists = await db.execute(select(LoyaltyTier).where(LoyaltyTier.code == code))
            tier = exists.scalar_one_or_none()
            if not tier:
                db.add(
                    LoyaltyTier(
                        code=code,
                        name=name,
                        min_lifetime_coins=min_c,
                        max_lifetime_coins=max_c,
                        sort_order=order,
                        status="active",
                    )
                )
            else:
                tier.name = name
                tier.min_lifetime_coins = min_c
                tier.max_lifetime_coins = max_c
                tier.sort_order = order
                tier.status = "active"

        settings_defaults = {
            "coins_per_rupee": ("10", "int", "Travel Coins required for INR 1 redemption value."),
            "coin_expiry_months": ("24", "int", "Standard coin expiry duration in months."),
            "minimum_redemption_coins": ("500", "int", "Minimum Travel Coins required before redemption."),
            "partial_redemption_allowed": ("true", "bool", "Allow partial reward or booking redemptions when supported."),
            "max_redemption_per_booking": ("", "int", "Optional maximum Travel Coins redeemable per booking."),
        }
        for key, (value, value_type, description) in settings_defaults.items():
            result = await db.execute(select(LoyaltyProgramSetting).where(LoyaltyProgramSetting.setting_key == key))
            setting = result.scalar_one_or_none()
            if not setting:
                db.add(
                    LoyaltyProgramSetting(
                        setting_key=key,
                        setting_value=value,
                        value_type=value_type,
                        description=description,
                        is_active=True,
                    )
                )

        missions_data = [
            ("COMPLETE_PROFILE", "Complete Profile", 50),
            ("UPLOAD_REVIEW", "Upload Review", 100),
            ("UPLOAD_REEL", "Upload Reel", 200),
            ("UPLOAD_PHOTO", "Upload Photo", 50),
            ("REFER_FRIEND", "Refer Friend", 500),
            ("BIRTHDAY_BONUS", "Birthday Bonus", 100),
        ]
        now = datetime.now(timezone.utc)
        for code, title, coins in missions_data:
            m_exists = await db.execute(select(Mission).where(Mission.code == code))
            mission = m_exists.scalar_one_or_none()
            if not mission:
                mission = Mission(code=code, title=title, is_one_time=True)
                db.add(mission)
                await db.flush()
                db.add(
                    MissionRewardRule(
                        mission_id=mission.id, coins_awarded=coins, effective_from=now, status="active"
                    )
                )

        ugc_rewards = [
            (UgcType.PHOTO, 50),
            (UgcType.REVIEW_SCREENSHOT, 100),
            (UgcType.TESTIMONIAL, 150),
            (UgcType.VIDEO, 200),
            (UgcType.REEL, 250),
        ]
        for ut, coins in ugc_rewards:
            r = await db.execute(select(UgcRewardRule).where(UgcRewardRule.ugc_type == ut))
            if not r.scalar_one_or_none():
                db.add(UgcRewardRule(ugc_type=ut, coins_awarded=coins, effective_from=now, status="active"))
            lim = await db.execute(select(UgcSubmissionLimit).where(UgcSubmissionLimit.ugc_type == ut))
            if not lim.scalar_one_or_none():
                db.add(UgcSubmissionLimit(ugc_type=ut, daily_limit=5, monthly_limit=20))

        ref_rule = await db.execute(select(ReferralRewardRule).limit(1))
        if not ref_rule.scalar_one_or_none():
            db.add(ReferralRewardRule(qualified_coins=500, effective_from=now, status="active"))

        brackets = [
            (Decimal("10000"), Decimal("49999.99"), 100),
            (Decimal("50000"), Decimal("99999.99"), 250),
            (Decimal("100000"), Decimal("249999.99"), 500),
            (Decimal("250000"), None, 1000),
        ]
        for min_a, max_a, coins in brackets:
            db.add(
                BookingBonusBracket(
                    min_amount_inr=min_a,
                    max_amount_inr=max_a,
                    coins_awarded=coins,
                    effective_from=now,
                    status="active",
                )
            )

        rewards = [
            ("10% Discount Voucher", "discount_voucher", 200, True, None),
            ("Airport Lounge Pass", "lounge_pass", 1500, False, 50),
        ]
        for title, rtype, cost, unlimited, inv in rewards:
            exists = await db.execute(select(RewardCatalog).where(RewardCatalog.title == title))
            if not exists.scalar_one_or_none():
                db.add(
                    RewardCatalog(
                        title=title,
                        reward_type=rtype,
                        cost_coins=cost,
                        unlimited_inventory=unlimited,
                        inventory_count=inv,
                        inventory_remaining=inv,
                    )
                )

        legacy_campaign = await db.execute(select(Campaign).where(Campaign.name == "Japan Launch", Campaign.deleted_at.is_(None)))
        legacy = legacy_campaign.scalar_one_or_none()
        if legacy:
            legacy.deleted_at = now
            legacy.status = "archived"

        campaigns = [
            {
                "name": "Japan Launch Campaign",
                "description": "Reward customers for early interest in Japan itineraries, content submissions, and referral activity.",
                "type": CampaignType.DESTINATION_LAUNCH,
                "eligibility_type": CampaignEligibilityType.ALL_CUSTOMERS,
                "reward_coins": 750,
                "tasks": ["Join the campaign", "Upload a Japan travel photo", "Refer a travel friend"],
                "status": "active",
                "start_at": now - timedelta(days=7),
                "end_at": now + timedelta(days=60),
            },
            {
                "name": "Summer Escape Campaign",
                "description": "Encourage summer trip planning with Travel Coins for profile completion and campaign missions.",
                "type": CampaignType.FESTIVAL,
                "eligibility_type": CampaignEligibilityType.ENROLLED_ONLY,
                "reward_coins": 500,
                "tasks": ["Enroll in campaign", "Complete profile", "Submit a summer travel testimonial"],
                "status": "active",
                "start_at": now - timedelta(days=3),
                "end_at": now + timedelta(days=45),
            },
            {
                "name": "Insider Travel Deal",
                "description": "Invite-only campaign for high-intent travellers and partner-led private travel offers.",
                "type": CampaignType.INSIDER,
                "eligibility_type": CampaignEligibilityType.INVITE_ONLY,
                "reward_coins": 1000,
                "tasks": ["Accept invitation", "Confirm travel interest", "Share preferred destination"],
                "status": "active",
                "start_at": now,
                "end_at": now + timedelta(days=30),
            },
            {
                "name": "Festive Travel Rewards",
                "description": "Seasonal travel retention campaign for festive booking and UGC engagement.",
                "type": CampaignType.FESTIVAL,
                "eligibility_type": CampaignEligibilityType.ALL_CUSTOMERS,
                "reward_coins": 650,
                "tasks": ["Upload festive travel photo", "Submit review screenshot", "Redeem a travel reward"],
                "status": "draft",
                "start_at": now + timedelta(days=15),
                "end_at": now + timedelta(days=90),
            },
        ]
        for item in campaigns:
            existing = await db.execute(select(Campaign).where(Campaign.name == item["name"]))
            campaign = existing.scalar_one_or_none()
            if not campaign:
                db.add(Campaign(**item))
            else:
                for key, value in item.items():
                    setattr(campaign, key, value)

        admin_role = await db.execute(select(AdminRole).where(func.lower(AdminRole.name) == "admin"))
        role = admin_role.scalar_one_or_none()
        if not role:
            role = AdminRole(name="admin")
            db.add(role)
            await db.flush()
        else:
            role.name = "admin"
            await db.flush()

        admin_exists = await db.execute(select(AdminUser).where(func.lower(AdminUser.email) == DEFAULT_ADMIN_EMAIL.lower()))
        admin = admin_exists.scalar_one_or_none()
        if not admin:
            admin = AdminUser(
                email=DEFAULT_ADMIN_EMAIL.lower(),
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                status="active",
            )
            db.add(admin)
            await db.flush()
        else:
            admin.email = DEFAULT_ADMIN_EMAIL.lower()
            admin.status = "active"
            admin.deleted_at = None
            admin.password_hash = hash_password(DEFAULT_ADMIN_PASSWORD)
            await db.flush()

        admin_role_link = await db.execute(
            select(AdminUserRole).where(AdminUserRole.admin_user_id == admin.id, AdminUserRole.role_id == role.id)
        )
        if not admin_role_link.scalar_one_or_none():
            db.add(AdminUserRole(admin_user_id=admin.id, role_id=role.id))
        print(f"Default admin ensured: {DEFAULT_ADMIN_EMAIL.lower()} / role=admin / status=active")

        await db.commit()
    await engine.dispose()
    print("Seed completed.")


if __name__ == "__main__":
    asyncio.run(seed())
