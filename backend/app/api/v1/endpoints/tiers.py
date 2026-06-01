from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_customer
from app.db.session import get_db
from app.models.customer import Customer
from app.models.tier import CustomerCurrentTier, CustomerTierHistory, LoyaltyTier
from app.schemas.common import ApiResponse
from app.services.wallet_service import WalletService
from pydantic import BaseModel

router = APIRouter()


class TierCurrentResponse(BaseModel):
    tier_code: str
    tier_name: str
    lifetime_coins_earned: int
    set_at: str | None


class TierHistoryItem(BaseModel):
    tier_code: str
    lifetime_coins_at_upgrade: int
    source: str
    achieved_at: str


@router.get("/current", response_model=ApiResponse[TierCurrentResponse])
async def current_tier(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    wallet = WalletService(db)
    balance = await wallet.ensure_wallet_balance(customer.id)
    result = await db.execute(
        select(CustomerCurrentTier, LoyaltyTier)
        .join(LoyaltyTier, CustomerCurrentTier.tier_id == LoyaltyTier.id)
        .where(CustomerCurrentTier.customer_id == customer.id)
    )
    row = result.first()
    if not row:
        from app.services.tier_service import TierService

        tier_svc = TierService(db)
        code = tier_svc.tier_for_lifetime(balance.lifetime_coins_earned)
        tier = await tier_svc.get_tier_by_code(code)
        return ApiResponse(
            data=TierCurrentResponse(
                tier_code=code.value,
                tier_name=tier.name if tier else code.value,
                lifetime_coins_earned=balance.lifetime_coins_earned,
                set_at=None,
            )
        )
    current, tier = row
    return ApiResponse(
        data=TierCurrentResponse(
            tier_code=tier.code.value,
            tier_name=tier.name,
            lifetime_coins_earned=balance.lifetime_coins_earned,
            set_at=current.set_at.isoformat() if current.set_at else None,
        )
    )


@router.get("/history", response_model=ApiResponse[list[TierHistoryItem]])
async def tier_history(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
):
    result = await db.execute(
        select(CustomerTierHistory, LoyaltyTier)
        .join(LoyaltyTier, CustomerTierHistory.tier_id == LoyaltyTier.id)
        .where(CustomerTierHistory.customer_id == customer.id)
        .order_by(CustomerTierHistory.achieved_at.desc())
        .limit(limit)
    )
    items = []
    for hist, tier in result.all():
        items.append(
            TierHistoryItem(
                tier_code=tier.code.value,
                lifetime_coins_at_upgrade=hist.lifetime_coins_at_upgrade,
                source=hist.source,
                achieved_at=hist.achieved_at.isoformat(),
            )
        )
    return ApiResponse(data=items)
