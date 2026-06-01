from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_customer
from app.db.session import get_db
from app.models.customer import Customer
from app.models.referral import ReferralAttribution, ReferralStatusHistory
from app.schemas.common import ApiResponse
from app.services.referral_service import ReferralService

router = APIRouter()


class ReferralMeResponse(BaseModel):
    referral_code: str
    referral_link: str
    status_summary: dict[str, int]


class ReferralTrackRequest(BaseModel):
    referral_code: str
    referral_source: str
    referral_link: str | None = None
    referred_phone: str | None = None
    referred_email: str | None = None
    device_fingerprint: str | None = None


class ReferralStatusItem(BaseModel):
    referral_attribution_id: str
    status: str
    referred_phone: str | None
    qualified_at: str | None
    reward_issued_at: str | None


@router.get("/me", response_model=ApiResponse[ReferralMeResponse])
async def my_referral(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ReferralService(db)
    code = await svc.get_or_create_code(customer.id)
    summary: dict[str, int] = {}
    counts = await db.execute(
        select(ReferralAttribution.status, func.count())
        .where(ReferralAttribution.referrer_customer_id == customer.id)
        .group_by(ReferralAttribution.status)
    )
    for status, count in counts.all():
        summary[status.value if hasattr(status, "value") else str(status)] = count
    return ApiResponse(
        data=ReferralMeResponse(
            referral_code=code.code,
            referral_link=f"https://tripoly.app/r/{code.code}",
            status_summary=summary,
        )
    )


@router.post("/track", response_model=ApiResponse[dict])
async def track_referral(body: ReferralTrackRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    svc = ReferralService(db)
    attr = await svc.track_referral(
        referral_code=body.referral_code,
        referral_source=body.referral_source,
        referred_phone=body.referred_phone,
        referred_email=body.referred_email,
        referral_link=body.referral_link,
        device_fingerprint=body.device_fingerprint,
    )
    return ApiResponse(data={"referral_attribution_id": str(attr.id), "status": attr.status.value})


@router.get("/status", response_model=ApiResponse[list[ReferralStatusItem]])
async def referral_status(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
):
    result = await db.execute(
        select(ReferralAttribution)
        .where(ReferralAttribution.referrer_customer_id == customer.id)
        .order_by(ReferralAttribution.created_at.desc())
        .limit(limit)
    )
    items = [
        ReferralStatusItem(
            referral_attribution_id=str(a.id),
            status=a.status.value,
            referred_phone=a.referred_phone,
            qualified_at=a.qualified_at.isoformat() if a.qualified_at else None,
            reward_issued_at=a.reward_issued_at.isoformat() if a.reward_issued_at else None,
        )
        for a in result.scalars().all()
    ]
    return ApiResponse(data=items)
