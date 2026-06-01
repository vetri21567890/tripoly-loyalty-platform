from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_customer
from app.db.session import get_db
from app.models.customer import Customer, CustomerProfile, CustomerTravelPreferences
from app.schemas.common import ApiResponse
from app.schemas.profile import (
    CompleteProfileResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    TravelPreferencesUpdateRequest,
    WalletBalanceBrief,
)
from app.services.earning_service import EarningService
from app.services.referral_service import ReferralService
from app.services.wallet_service import WalletService

router = APIRouter()


@router.get("/me/profile", response_model=ApiResponse[ProfileResponse])
async def get_profile(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(CustomerProfile).where(CustomerProfile.customer_id == customer.id))
    profile = result.scalar_one_or_none()
    prefs_result = await db.execute(
        select(CustomerTravelPreferences).where(CustomerTravelPreferences.customer_id == customer.id)
    )
    prefs = prefs_result.scalar_one_or_none()
    return ApiResponse(
        data=ProfileResponse(
            customer_id=customer.id,
            first_name=profile.first_name if profile else None,
            last_name=profile.last_name if profile else None,
            birthday=profile.birthday if profile else None,
            avatar_object_key=profile.avatar_object_key if profile else None,
            profile_completed_at=profile.profile_completed_at if profile else None,
            travel_preferences=prefs.preferences_jsonb if prefs else {},
        )
    )


@router.put("/me/profile", response_model=ApiResponse[ProfileResponse])
async def update_profile(
    body: ProfileUpdateRequest,
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(CustomerProfile).where(CustomerProfile.customer_id == customer.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = CustomerProfile(customer_id=customer.id)
        db.add(profile)
    profile.first_name = body.first_name
    profile.last_name = body.last_name
    profile.birthday = body.birthday
    await db.flush()
    return await get_profile(customer, db)


@router.put("/me/travel-preferences", response_model=ApiResponse[dict])
async def update_travel_preferences(
    body: TravelPreferencesUpdateRequest,
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(CustomerTravelPreferences).where(CustomerTravelPreferences.customer_id == customer.id)
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = CustomerTravelPreferences(customer_id=customer.id, preferences_jsonb=body.preferences)
        db.add(prefs)
    else:
        prefs.preferences_jsonb = body.preferences
    await db.flush()
    return ApiResponse(data={"preferences": prefs.preferences_jsonb})


@router.post("/me/complete-profile", response_model=ApiResponse[CompleteProfileResponse])
async def complete_profile(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(CustomerProfile).where(CustomerProfile.customer_id == customer.id))
    profile = result.scalar_one_or_none()
    if not profile or not profile.first_name:
        from fastapi import HTTPException

        raise HTTPException(400, detail={"code": "VALIDATION_ERROR", "message": "Profile incomplete"})
    if profile.profile_completed_at:
        from fastapi import HTTPException

        raise HTTPException(409, detail={"code": "CONFLICT", "message": "Profile already completed"})

    profile.profile_completed_at = datetime.now(timezone.utc)
    earning = EarningService(db)
    coins, _ = await earning.issue_complete_profile_bonus(customer.id)
    referral = ReferralService(db)
    await referral.on_profile_completed(customer.id)

    wallet = WalletService(db)
    balance = await wallet.ensure_wallet_balance(customer.id)
    return ApiResponse(
        data=CompleteProfileResponse(
            profile_completed=True,
            coins_awarded=coins,
            wallet_balance=WalletBalanceBrief(
                available_coins=balance.available_coins,
                lifetime_coins_earned=balance.lifetime_coins_earned,
            ),
        )
    )
