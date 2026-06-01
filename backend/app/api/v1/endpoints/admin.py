from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.security import create_access_token, hash_password
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.auth import AdminRole, AdminUser, AdminUserRole
from app.models.booking import BookingEvent
from app.models.campaign import Campaign, CampaignParticipation
from app.models.customer import Customer, CustomerProfile
from app.models.earning_rules import BirthdayBonusRule, BookingBonusBracket, ReferralRewardRule
from app.models.enums import (
    CampaignEligibilityType,
    CampaignType,
    LoyaltyTierCode,
    ReferralStatus,
    RewardStatus,
    UgcAttemptStatus,
    UgcModerationDecision,
    UgcType,
)
from app.models.mission import Mission, MissionRewardRule
from app.models.notification import InAppNotification
from app.models.referral import ReferralAttribution
from app.models.rewards import RewardCatalog, RewardRedemption
from app.models.tier import LoyaltyTier
from app.models.ugc import UgcAttempt, UgcRewardRule, UgcSubmissionLimit, UgcThread
from app.models.wallet import CoinGrant, CoinTransaction, WalletBalance
from app.services.program_settings_service import ProgramSettingsService
from app.schemas.common import ApiResponse
from app.services.ugc_service import UgcService

router = APIRouter()


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class UgcModerateRequest(BaseModel):
    decision: UgcModerationDecision
    rejection_reason: str | None = None


class RewardUpsertRequest(BaseModel):
    reward_catalog_id: UUID | None = None
    title: str
    description: str | None = None
    reward_type: str
    cost_coins: int = Field(gt=0)
    unlimited_inventory: bool
    inventory_count: int | None = None


class UgcRuleUpsertRequest(BaseModel):
    ugc_type: UgcType
    coins_awarded: int = Field(gt=0)


class UgcLimitUpsertRequest(BaseModel):
    ugc_type: UgcType
    daily_limit: int = Field(ge=0)
    monthly_limit: int = Field(ge=0)


class TierUpsertRequest(BaseModel):
    code: LoyaltyTierCode
    name: str
    min_lifetime_coins: int = Field(ge=0)
    max_lifetime_coins: int | None = Field(default=None, ge=0)
    benefits: dict = Field(default_factory=dict)
    status: str = Field(default="active")
    sort_order: int = Field(ge=1)


class WalletRulesUpdateRequest(BaseModel):
    coins_per_rupee: int = Field(gt=0)
    coin_expiry_months: int = Field(gt=0)
    minimum_redemption_coins: int = Field(ge=0)
    partial_redemption_allowed: bool = True
    max_redemption_per_booking: int | None = Field(default=None, ge=0)


class CampaignUpsertRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    type: CampaignType = CampaignType.INSIDER
    eligibility_type: CampaignEligibilityType = CampaignEligibilityType.ALL_CUSTOMERS
    reward_coins: int = Field(default=0, ge=0)
    tasks: list[str] = Field(default_factory=list)
    status: str = Field(default="draft")
    start_at: datetime | None = None
    end_at: datetime | None = None


class CustomerCreateRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    password: str | None = Field(default=None, min_length=8)
    first_name: str | None = None
    last_name: str | None = None
    status: str = Field(default="active")


def normalize_campaign_status(status: str) -> str:
    normalized = status.strip().lower()
    allowed = {"draft", "active", "ended", "archived"}
    if normalized not in allowed:
        raise HTTPException(422, detail={"code": "VALIDATION_ERROR", "message": "Campaign status must be draft, active, ended, or archived"})
    return normalized


def normalize_customer_status(status: str) -> str:
    normalized = status.strip().lower()
    allowed = {"active", "inactive", "blocked"}
    if normalized not in allowed:
        raise HTTPException(422, detail={"code": "VALIDATION_ERROR", "message": "Customer status must be active, inactive, or blocked"})
    return normalized


def iso(value):
    return value.isoformat() if value else None


@router.post("/auth/login", response_model=ApiResponse[dict])
async def admin_login(body: AdminLoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    from app.core.security import verify_password

    result = await db.execute(
        select(AdminUser)
        .join(AdminUserRole, AdminUserRole.admin_user_id == AdminUser.id)
        .join(AdminRole, AdminRole.id == AdminUserRole.role_id)
        .where(
            func.lower(AdminUser.email) == body.email.strip().lower(),
            AdminUser.status == "active",
            AdminRole.name == "admin",
        )
    )
    admin = result.scalar_one_or_none()
    if not admin or not verify_password(body.password, admin.password_hash):
        raise HTTPException(401, detail={"code": "AUTH_INVALID_TOKEN", "message": "Invalid credentials"})
    token = create_access_token(admin.id, role="admin")
    return ApiResponse(data={"access_token": token, "token_type": "bearer"})


@router.get("/customers", response_model=ApiResponse[list[dict]])
async def list_customers(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 100,
):
    result = await db.execute(
        select(Customer, CustomerProfile, WalletBalance)
        .outerjoin(CustomerProfile, CustomerProfile.customer_id == Customer.id)
        .outerjoin(WalletBalance, WalletBalance.customer_id == Customer.id)
        .where(Customer.deleted_at.is_(None))
        .order_by(Customer.created_at.desc())
        .limit(limit)
    )
    return ApiResponse(
        data=[
            {
                "customer_id": str(c.id),
                "email": c.email,
                "phone": c.phone,
                "first_name": profile.first_name if profile else None,
                "last_name": profile.last_name if profile else None,
                "status": c.status,
                "available_coins": balance.available_coins if balance else 0,
                "lifetime_coins_earned": balance.lifetime_coins_earned if balance else 0,
                "created_at": c.created_at.isoformat(),
            }
            for c, profile, balance in result.all()
        ]
    )


@router.post("/customers", response_model=ApiResponse[dict])
async def create_customer(
    body: CustomerCreateRequest,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    email = body.email.strip().lower() if body.email else None
    phone = body.phone.strip() if body.phone else None
    if not email and not phone:
        raise HTTPException(422, detail={"code": "VALIDATION_ERROR", "message": "Email or phone is required"})
    if email:
        exists = await db.scalar(select(Customer).where(func.lower(Customer.email) == email, Customer.deleted_at.is_(None)))
        if exists:
            raise HTTPException(409, detail={"code": "CONFLICT", "message": "Customer email already exists"})
    if phone:
        exists = await db.scalar(select(Customer).where(Customer.phone == phone, Customer.deleted_at.is_(None)))
        if exists:
            raise HTTPException(409, detail={"code": "CONFLICT", "message": "Customer phone already exists"})

    customer = Customer(
        email=email,
        phone=phone,
        password_hash=hash_password(body.password) if body.password else None,
        status=normalize_customer_status(body.status),
    )
    db.add(customer)
    await db.flush()
    profile = CustomerProfile(
        customer_id=customer.id,
        first_name=body.first_name.strip() if body.first_name else None,
        last_name=body.last_name.strip() if body.last_name else None,
    )
    db.add(profile)
    db.add(WalletBalance(customer_id=customer.id, available_coins=0, expired_coins=0, redeemed_coins_to_date=0, lifetime_coins_earned=0))
    await db.flush()
    return ApiResponse(
        message="Customer created",
        data={
            "customer_id": str(customer.id),
            "email": customer.email,
            "phone": customer.phone,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "status": customer.status,
            "available_coins": 0,
            "lifetime_coins_earned": 0,
            "created_at": customer.created_at.isoformat(),
        },
    )


@router.get("/campaigns", response_model=ApiResponse[list[dict]])
async def list_admin_campaigns(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Campaign, func.count(CampaignParticipation.id))
        .outerjoin(
            CampaignParticipation,
            (CampaignParticipation.campaign_id == Campaign.id) & (CampaignParticipation.deleted_at.is_(None)),
        )
        .where(Campaign.deleted_at.is_(None))
        .group_by(Campaign.id)
        .order_by(Campaign.created_at.desc())
    )
    return ApiResponse(
        data=[
            {
                "campaign_id": str(c.id),
                "name": c.name,
                "description": c.description,
                "type": c.type.value,
                "eligibility_type": c.eligibility_type.value,
                "reward_coins": c.reward_coins,
                "tasks": c.tasks or [],
                "status": c.status,
                "start_at": c.start_at.isoformat() if c.start_at else None,
                "end_at": c.end_at.isoformat() if c.end_at else None,
                "participants": participants,
            }
            for c, participants in result.all()
        ]
    )


@router.post("/campaigns", response_model=ApiResponse[dict])
async def create_admin_campaign(
    body: CampaignUpsertRequest,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    campaign = Campaign(
        name=body.name.strip(),
        description=body.description.strip() if body.description else None,
        type=body.type,
        eligibility_type=body.eligibility_type,
        reward_coins=body.reward_coins,
        tasks=[task.strip() for task in body.tasks if task.strip()],
        status=normalize_campaign_status(body.status),
        start_at=body.start_at,
        end_at=body.end_at,
    )
    db.add(campaign)
    await db.flush()
    return ApiResponse(
        message="Campaign created",
        data={
            "campaign_id": str(campaign.id),
            "name": campaign.name,
            "description": campaign.description,
            "type": campaign.type.value,
            "eligibility_type": campaign.eligibility_type.value,
            "reward_coins": campaign.reward_coins,
            "tasks": campaign.tasks or [],
            "status": campaign.status,
            "start_at": iso(campaign.start_at),
            "end_at": iso(campaign.end_at),
        },
    )


@router.put("/campaigns/{campaign_id}", response_model=ApiResponse[dict])
async def update_admin_campaign(
    campaign_id: UUID,
    body: CampaignUpsertRequest,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id, Campaign.deleted_at.is_(None)))
    if not campaign:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    campaign.name = body.name.strip()
    campaign.description = body.description.strip() if body.description else None
    campaign.type = body.type
    campaign.eligibility_type = body.eligibility_type
    campaign.reward_coins = body.reward_coins
    campaign.tasks = [task.strip() for task in body.tasks if task.strip()]
    campaign.status = normalize_campaign_status(body.status)
    campaign.start_at = body.start_at
    campaign.end_at = body.end_at
    await db.flush()
    return ApiResponse(
        message="Campaign updated",
        data={
            "campaign_id": str(campaign.id),
            "name": campaign.name,
            "description": campaign.description,
            "type": campaign.type.value,
            "eligibility_type": campaign.eligibility_type.value,
            "reward_coins": campaign.reward_coins,
            "tasks": campaign.tasks or [],
            "status": campaign.status,
            "start_at": iso(campaign.start_at),
            "end_at": iso(campaign.end_at),
        },
    )


@router.get("/missions", response_model=ApiResponse[list[dict]])
async def list_admin_missions(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Mission, MissionRewardRule)
        .outerjoin(
            MissionRewardRule,
            (MissionRewardRule.mission_id == Mission.id) & (MissionRewardRule.status == "active"),
        )
        .where(Mission.deleted_at.is_(None))
        .order_by(Mission.created_at.desc())
    )
    return ApiResponse(
        data=[
            {
                "mission_id": str(m.id),
                "code": m.code,
                "title": m.title,
                "is_one_time": m.is_one_time,
                "status": m.status,
                "coins_awarded": rule.coins_awarded if rule else 0,
            }
            for m, rule in result.all()
        ]
    )


@router.get("/referrals", response_model=ApiResponse[list[dict]])
async def list_admin_referrals(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 100,
):
    result = await db.execute(select(ReferralAttribution).order_by(ReferralAttribution.created_at.desc()).limit(limit))
    return ApiResponse(
        data=[
            {
                "referral_attribution_id": str(r.id),
                "referrer_customer_id": str(r.referrer_customer_id),
                "referred_customer_id": str(r.referred_customer_id) if r.referred_customer_id else None,
                "referred_email": r.referred_email,
                "referred_phone": r.referred_phone,
                "referral_source": r.referral_source,
                "status": r.status.value,
                "invited_at": r.invited_at.isoformat(),
                "qualified_at": r.qualified_at.isoformat() if r.qualified_at else None,
                "reward_issued_at": r.reward_issued_at.isoformat() if r.reward_issued_at else None,
            }
            for r in result.scalars().all()
        ]
    )


@router.get("/wallet/transactions", response_model=ApiResponse[list[dict]])
async def list_admin_wallet_transactions(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 100,
):
    result = await db.execute(select(CoinTransaction).order_by(CoinTransaction.created_at.desc()).limit(limit))
    return ApiResponse(
        data=[
            {
                "transaction_id": str(t.id),
                "customer_id": str(t.customer_id),
                "direction": t.direction.value,
                "amount": t.amount,
                "reason_code": t.reason_code,
                "created_at": t.created_at.isoformat(),
            }
            for t in result.scalars().all()
        ]
    )


@router.get("/wallet/grants", response_model=ApiResponse[list[dict]])
async def list_admin_coin_grants(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 100,
):
    result = await db.execute(select(CoinGrant).order_by(CoinGrant.created_at.desc()).limit(limit))
    return ApiResponse(
        data=[
            {
                "coin_grant_id": str(g.id),
                "customer_id": str(g.customer_id),
                "grant_source": g.grant_source,
                "amount_total": g.amount_total,
                "amount_remaining": g.amount_remaining,
                "status": g.status.value,
                "expiry_date": g.expiry_date.isoformat() if g.expiry_date else None,
            }
            for g in result.scalars().all()
        ]
    )


@router.get("/ugc/attempts", response_model=ApiResponse[list[dict]])
async def list_admin_ugc_attempts(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 100,
):
    result = await db.execute(
        select(UgcAttempt, UgcThread)
        .join(UgcThread, UgcThread.id == UgcAttempt.ugc_thread_id)
        .order_by(UgcAttempt.created_at.desc())
        .limit(limit)
    )
    return ApiResponse(
        data=[
            {
                "ugc_attempt_id": str(a.id),
                "customer_id": str(t.customer_id),
                "ugc_type": t.ugc_type.value,
                "destination": t.destination,
                "status": a.status.value,
                "media_object_key": a.media_object_key,
                "rejection_reason": a.rejection_reason,
                "created_at": a.created_at.isoformat(),
            }
            for a, t in result.all()
        ]
    )


@router.get("/earning-rules/ugc", response_model=ApiResponse[list[dict]])
async def list_ugc_rules(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rewards = await db.execute(select(UgcRewardRule).where(UgcRewardRule.deleted_at.is_(None)))
    limits = await db.execute(select(UgcSubmissionLimit).where(UgcSubmissionLimit.deleted_at.is_(None)))
    limit_by_type = {lim.ugc_type: lim for lim in limits.scalars().all()}
    return ApiResponse(
        data=[
            {
                "ugc_type": r.ugc_type.value,
                "coins_awarded": r.coins_awarded,
                "status": r.status,
                "daily_limit": limit_by_type.get(r.ugc_type).daily_limit if r.ugc_type in limit_by_type else None,
                "monthly_limit": limit_by_type.get(r.ugc_type).monthly_limit if r.ugc_type in limit_by_type else None,
            }
            for r in rewards.scalars().all()
        ]
    )


@router.get("/points-engine", response_model=ApiResponse[dict])
async def points_engine(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    booking = await db.execute(select(BookingBonusBracket).where(BookingBonusBracket.deleted_at.is_(None)).order_by(BookingBonusBracket.min_amount_inr))
    ugc = await db.execute(select(UgcRewardRule).where(UgcRewardRule.deleted_at.is_(None)).order_by(UgcRewardRule.ugc_type))
    referral = await db.execute(select(ReferralRewardRule).where(ReferralRewardRule.deleted_at.is_(None)).order_by(ReferralRewardRule.effective_from.desc()))
    birthday = await db.execute(select(BirthdayBonusRule).where(BirthdayBonusRule.deleted_at.is_(None)).order_by(BirthdayBonusRule.effective_from.desc()))
    mission_rules = await db.execute(
        select(Mission, MissionRewardRule)
        .join(MissionRewardRule, MissionRewardRule.mission_id == Mission.id)
        .where(Mission.deleted_at.is_(None), MissionRewardRule.deleted_at.is_(None))
        .order_by(Mission.code)
    )
    return ApiResponse(
        data={
            "booking_bonus_rules": [
                {
                    "id": str(r.id),
                    "min_amount_inr": str(r.min_amount_inr),
                    "max_amount_inr": str(r.max_amount_inr) if r.max_amount_inr else None,
                    "coins_awarded": r.coins_awarded,
                    "status": r.status,
                    "effective_from": iso(r.effective_from),
                }
                for r in booking.scalars().all()
            ],
            "ugc_reward_rules": [
                {"id": str(r.id), "ugc_type": r.ugc_type.value, "coins_awarded": r.coins_awarded, "status": r.status}
                for r in ugc.scalars().all()
            ],
            "referral_reward_rules": [
                {"id": str(r.id), "qualified_coins": r.qualified_coins, "status": r.status, "effective_from": iso(r.effective_from)}
                for r in referral.scalars().all()
            ],
            "birthday_bonus_rules": [
                {"id": str(r.id), "coins_awarded": r.coins_awarded, "award_frequency": r.award_frequency, "status": r.status}
                for r in birthday.scalars().all()
            ],
            "mission_reward_rules": [
                {
                    "mission_code": m.code,
                    "mission_title": m.title,
                    "coins_awarded": r.coins_awarded,
                    "status": r.status,
                    "effective_from": iso(r.effective_from),
                }
                for m, r in mission_rules.all()
            ],
        }
    )


@router.get("/tiers", response_model=ApiResponse[list[dict]])
async def list_admin_tiers(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(LoyaltyTier).order_by(LoyaltyTier.sort_order))
    return ApiResponse(
        data=[
            {
                "tier_id": str(t.id),
                "code": t.code.value,
                "name": t.name,
                "min_lifetime_coins": t.min_lifetime_coins,
                "max_lifetime_coins": t.max_lifetime_coins,
                "benefits": t.perks_jsonb or {},
                "status": t.status,
                "sort_order": t.sort_order,
            }
            for t in result.scalars().all()
        ]
    )


@router.post("/tiers", response_model=ApiResponse[dict])
async def create_admin_tier(
    body: TierUpsertRequest,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    existing = await db.scalar(select(LoyaltyTier).where(LoyaltyTier.code == body.code))
    if existing:
        raise HTTPException(409, detail={"code": "CONFLICT", "message": "Tier code already exists"})
    tier = LoyaltyTier(
        code=body.code,
        name=body.name,
        min_lifetime_coins=body.min_lifetime_coins,
        max_lifetime_coins=body.max_lifetime_coins,
        perks_jsonb=body.benefits,
        status=body.status,
        sort_order=body.sort_order,
    )
    db.add(tier)
    await db.flush()
    return ApiResponse(data={"tier_id": str(tier.id)})


@router.put("/tiers/{tier_id}", response_model=ApiResponse[dict])
async def update_admin_tier(
    tier_id: UUID,
    body: TierUpsertRequest,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tier = await db.scalar(select(LoyaltyTier).where(LoyaltyTier.id == tier_id))
    if not tier:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Tier not found"})
    tier.code = body.code
    tier.name = body.name
    tier.min_lifetime_coins = body.min_lifetime_coins
    tier.max_lifetime_coins = body.max_lifetime_coins
    tier.perks_jsonb = body.benefits
    tier.status = body.status
    tier.sort_order = body.sort_order
    await db.flush()
    return ApiResponse(data={"tier_id": str(tier.id), "status": tier.status})


@router.get("/rewards/redemptions", response_model=ApiResponse[list[dict]])
async def list_admin_redemptions(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 100,
):
    result = await db.execute(
        select(RewardRedemption, RewardCatalog)
        .join(RewardCatalog, RewardCatalog.id == RewardRedemption.reward_catalog_id)
        .order_by(RewardRedemption.redeemed_at.desc())
        .limit(limit)
    )
    return ApiResponse(
        data=[
            {
                "reward_redemption_id": str(r.id),
                "customer_id": str(r.customer_id),
                "reward_title": c.title,
                "coins_spent": r.coins_spent,
                "status": r.status.value,
                "redeemed_at": iso(r.redeemed_at),
                "voucher_code": (r.metadata_jsonb or {}).get("voucher_code"),
            }
            for r, c in result.all()
        ]
    )


@router.get("/travel/booking-webhooks", response_model=ApiResponse[list[dict]])
async def list_booking_webhooks(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 100,
):
    result = await db.execute(select(BookingEvent).order_by(BookingEvent.confirmed_at.desc()).limit(limit))
    return ApiResponse(
        data=[
            {
                "booking_event_id": str(b.id),
                "source_system": b.source_system,
                "source_booking_id": b.source_booking_id,
                "customer_id": str(b.customer_id),
                "confirmed_at": iso(b.confirmed_at),
                "booking_value_inr": str(b.booking_value_inr),
                "value_source": b.value_source.value,
                "coins_awarded": b.coins_awarded,
            }
            for b in result.scalars().all()
        ]
    )


@router.get("/travel/partner-integrations", response_model=ApiResponse[list[dict]])
async def partner_integrations(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    sources = await db.execute(select(BookingEvent.source_system, func.count()).group_by(BookingEvent.source_system))
    source_rows = sources.all()
    return ApiResponse(
        data=[
            {
                "integration": "Booking Webhooks",
                "connection_model": "API key + webhook",
                "status": "active",
                "events_received": sum(count for _, count in source_rows),
            },
            {
                "integration": "Customer Sync",
                "connection_model": "API key + webhook",
                "status": "available",
                "events_received": None,
            },
            {
                "integration": "Referral Validation",
                "connection_model": "API key + webhook",
                "status": "available",
                "events_received": None,
            },
            {
                "integration": "Partner Coin Issue",
                "connection_model": "API key + webhook",
                "status": "available",
                "events_received": None,
            },
        ]
    )


@router.get("/travel/activity-logs", response_model=ApiResponse[list[dict]])
async def travel_activity_logs(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 100,
):
    bookings = await db.execute(select(BookingEvent).order_by(BookingEvent.created_at.desc()).limit(limit))
    return ApiResponse(
        data=[
            {
                "activity_id": str(b.id),
                "activity_type": "booking_confirmed",
                "source_system": b.source_system,
                "customer_id": str(b.customer_id),
                "coins_awarded": b.coins_awarded,
                "created_at": iso(b.created_at),
            }
            for b in bookings.scalars().all()
        ]
    )


@router.get("/program-settings", response_model=ApiResponse[dict])
async def program_settings(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    referral_rule = await db.scalar(select(ReferralRewardRule).where(ReferralRewardRule.status == "active").order_by(ReferralRewardRule.effective_from.desc()).limit(1))
    ugc_limits = await db.execute(select(UgcSubmissionLimit).where(UgcSubmissionLimit.deleted_at.is_(None)))
    settings = ProgramSettingsService(db)
    rows = await settings.list_settings()
    settings_data = {row.setting_key: settings.parse_value(row.setting_value, row.value_type, None) for row in rows}
    return ApiResponse(
        data={
            "coins_per_rupee": settings_data.get("coins_per_rupee", 10),
            "coin_expiry_months": settings_data.get("coin_expiry_months", 24),
            "minimum_redemption_coins": settings_data.get("minimum_redemption_coins", 500),
            "partial_redemption_allowed": settings_data.get("partial_redemption_allowed", True),
            "max_redemption_per_booking": settings_data.get("max_redemption_per_booking"),
            "conversion_rule": f"{settings_data.get('coins_per_rupee', 10)} Travel Coins = ₹1",
            "referral_reward_amount": referral_rule.qualified_coins if referral_rule else 0,
            "ugc_approval_required": True,
            "campaign_eligibility_settings": ["all_customers", "enrolled_only", "invite_only"],
            "redemption_limits": "wallet_balance_and_inventory",
            "wallet_rules": "FIFO grant spending with expiry-aware balances",
            "ugc_limits": [
                {
                    "ugc_type": row.ugc_type.value,
                    "daily_limit": row.daily_limit,
                    "monthly_limit": row.monthly_limit,
                    "status": row.status,
                }
                for row in ugc_limits.scalars().all()
            ],
        }
    )


@router.put("/program-settings/wallet-rules", response_model=ApiResponse[dict])
async def update_wallet_rules(
    body: WalletRulesUpdateRequest,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    settings = ProgramSettingsService(db)
    await settings.set("coins_per_rupee", body.coins_per_rupee, "int")
    await settings.set("coin_expiry_months", body.coin_expiry_months, "int")
    await settings.set("minimum_redemption_coins", body.minimum_redemption_coins, "int")
    await settings.set("partial_redemption_allowed", body.partial_redemption_allowed, "bool")
    await settings.set("max_redemption_per_booking", body.max_redemption_per_booking, "int")
    return ApiResponse(
        data={
            "coins_per_rupee": body.coins_per_rupee,
            "coin_expiry_months": body.coin_expiry_months,
            "minimum_redemption_coins": body.minimum_redemption_coins,
            "partial_redemption_allowed": body.partial_redemption_allowed,
            "max_redemption_per_booking": body.max_redemption_per_booking,
            "conversion_rule": f"{body.coins_per_rupee} Travel Coins = ₹1",
        }
    )


@router.get("/performance", response_model=ApiResponse[dict])
async def loyalty_performance(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    active_customers = await db.scalar(select(func.count(Customer.id)).where(Customer.status == "active", Customer.deleted_at.is_(None)))
    total_issued = await db.scalar(select(func.coalesce(func.sum(WalletBalance.lifetime_coins_earned), 0)))
    total_redeemed = await db.scalar(select(func.coalesce(func.sum(WalletBalance.redeemed_coins_to_date), 0)))
    referrals_qualified = await db.scalar(select(func.count(ReferralAttribution.id)).where(ReferralAttribution.status.in_([ReferralStatus.QUALIFIED, ReferralStatus.REWARD_ISSUED])))
    ugc_submissions = await db.scalar(select(func.count(UgcAttempt.id)))
    redemptions = await db.scalar(select(func.count(RewardRedemption.id)).where(RewardRedemption.status == RewardStatus.COMPLETED))
    campaign_participation = await db.scalar(select(func.count(CampaignParticipation.id)))
    return ApiResponse(
        data={
            "active_customers": active_customers or 0,
            "total_coins_issued": total_issued or 0,
            "total_coins_redeemed": total_redeemed or 0,
            "referral_conversions": referrals_qualified or 0,
            "ugc_submissions": ugc_submissions or 0,
            "reward_redemptions": redemptions or 0,
            "campaign_participation": campaign_participation or 0,
            "repeat_engagement": (ugc_submissions or 0) + (campaign_participation or 0) + (referrals_qualified or 0),
        }
    )


@router.get("/reports/{report_key}", response_model=ApiResponse[dict])
async def report_summary(
    report_key: str,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    performance = await loyalty_performance(admin, db)
    base = performance.data
    report_map = {
        "customer-analytics": {"active_customers": base["active_customers"], "repeat_engagement": base["repeat_engagement"]},
        "wallet-analytics": {"total_coins_issued": base["total_coins_issued"], "total_coins_redeemed": base["total_coins_redeemed"]},
        "referral-analytics": {"referral_conversions": base["referral_conversions"]},
        "campaign-analytics": {"campaign_participation": base["campaign_participation"]},
        "ugc-analytics": {"ugc_submissions": base["ugc_submissions"]},
        "redemption-analytics": {"reward_redemptions": base["reward_redemptions"]},
    }
    if report_key not in report_map:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Report not found"})
    return ApiResponse(data={"report": report_key, "metrics": report_map[report_key]})


@router.get("/notifications", response_model=ApiResponse[list[dict]])
async def list_admin_notifications(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 100,
):
    result = await db.execute(select(InAppNotification).order_by(InAppNotification.created_at.desc()).limit(limit))
    return ApiResponse(
        data=[
            {
                "notification_id": str(n.id),
                "customer_id": str(n.customer_id),
                "type": n.type,
                "title": n.title,
                "body": n.body,
                "read_at": n.read_at.isoformat() if n.read_at else None,
                "created_at": n.created_at.isoformat(),
            }
            for n in result.scalars().all()
        ]
    )


@router.post("/ugc/{ugc_attempt_id}/moderate", response_model=ApiResponse[dict])
async def moderate_ugc(
    ugc_attempt_id: UUID,
    body: UgcModerateRequest,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = UgcService(db)
    attempt = await svc.moderate(ugc_attempt_id, admin.id, body.decision, body.rejection_reason)
    db.add(
        AuditLog(
            actor_admin_user_id=admin.id,
            action_type="UGC_MODERATE",
            entity_type="ugc_attempt",
            entity_id=ugc_attempt_id,
            metadata_jsonb={"decision": body.decision.value},
        )
    )
    return ApiResponse(data={"ugc_attempt_id": str(attempt.id), "status": attempt.status.value})


@router.post("/rewards/catalog", response_model=ApiResponse[dict])
async def upsert_reward(
    body: RewardUpsertRequest,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.reward_catalog_id:
        result = await db.execute(select(RewardCatalog).where(RewardCatalog.id == body.reward_catalog_id))
        reward = result.scalar_one_or_none()
        if not reward:
            raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Reward not found"})
    else:
        reward = RewardCatalog()
        db.add(reward)

    reward.title = body.title
    reward.description = body.description
    reward.reward_type = body.reward_type
    reward.cost_coins = body.cost_coins
    reward.unlimited_inventory = body.unlimited_inventory
    if body.unlimited_inventory:
        reward.inventory_count = None
        reward.inventory_remaining = None
    else:
        reward.inventory_count = body.inventory_count or 0
        reward.inventory_remaining = body.inventory_count or 0

    await db.flush()
    db.add(
        AuditLog(
            actor_admin_user_id=admin.id,
            action_type="REWARD_UPSERT",
            entity_type="reward_catalog",
            entity_id=reward.id,
        )
    )
    return ApiResponse(data={"reward_catalog_id": str(reward.id)})


@router.post("/earning-rules/ugc", response_model=ApiResponse[dict])
async def upsert_ugc_rule(
    body: UgcRuleUpsertRequest,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(UgcRewardRule).where(UgcRewardRule.ugc_type == body.ugc_type))
    rule = result.scalar_one_or_none()
    if not rule:
        rule = UgcRewardRule(ugc_type=body.ugc_type, effective_from=datetime.now(timezone.utc))
        db.add(rule)
    rule.coins_awarded = body.coins_awarded
    rule.status = "active"
    await db.flush()
    return ApiResponse(data={"ugc_type": body.ugc_type.value, "coins_awarded": body.coins_awarded})


@router.post("/earning-rules/ugc-limits", response_model=ApiResponse[dict])
async def upsert_ugc_limits(
    body: UgcLimitUpsertRequest,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(UgcSubmissionLimit).where(UgcSubmissionLimit.ugc_type == body.ugc_type))
    lim = result.scalar_one_or_none()
    if not lim:
        lim = UgcSubmissionLimit(ugc_type=body.ugc_type)
        db.add(lim)
    lim.daily_limit = body.daily_limit
    lim.monthly_limit = body.monthly_limit
    await db.flush()
    return ApiResponse(data={"ugc_type": body.ugc_type.value})


@router.get("/audit-logs", response_model=ApiResponse[list[dict]])
async def audit_logs(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    entity_type: str | None = None,
    limit: int = 50,
):
    q = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
    result = await db.execute(q)
    return ApiResponse(
        data=[
            {
                "id": str(a.id),
                "action_type": a.action_type,
                "entity_type": a.entity_type,
                "entity_id": str(a.entity_id) if a.entity_id else None,
                "created_at": a.created_at.isoformat(),
            }
            for a in result.scalars().all()
        ]
    )
