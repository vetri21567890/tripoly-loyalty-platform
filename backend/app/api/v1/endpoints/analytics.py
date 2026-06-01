from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.auth import AdminUser
from app.models.customer import Customer
from app.models.referral import ReferralAttribution
from app.models.enums import ReferralStatus
from app.models.wallet import WalletBalance, CoinTransaction
from app.models.enums import CoinTransactionDirection
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/summary", response_model=ApiResponse[dict])
async def analytics_summary(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    active_users = await db.scalar(
        select(func.count(Customer.id)).where(Customer.deleted_at.is_(None), Customer.status == "active")
    )
    lifetime_issued = await db.scalar(select(func.coalesce(func.sum(WalletBalance.lifetime_coins_earned), 0)))
    redeemed = await db.scalar(select(func.coalesce(func.sum(WalletBalance.redeemed_coins_to_date), 0)))
    referrals_qualified = await db.scalar(
        select(func.count(ReferralAttribution.id)).where(
            ReferralAttribution.status.in_([ReferralStatus.QUALIFIED, ReferralStatus.REWARD_ISSUED])
        )
    )
    return ApiResponse(
        data={
            "active_users": active_users or 0,
            "lifetime_coins_issued": lifetime_issued or 0,
            "coins_redeemed": redeemed or 0,
            "referrals_qualified": referrals_qualified or 0,
        }
    )
