from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_customer
from app.db.session import get_db
from app.models.campaign import Campaign, CampaignInvitation, CampaignParticipation
from app.models.customer import Customer
from app.models.enums import CampaignEligibilityType
from app.schemas.common import ApiResponse

router = APIRouter()


class CampaignItem(BaseModel):
    campaign_id: UUID
    name: str
    description: str | None = None
    type: str
    eligibility_type: str
    status: str
    reward_coins: int = 0
    tasks: list[str] = Field(default_factory=list)
    start_at: str | None
    end_at: str | None
    participation_status: str | None = None
    invitation_status: str | None = None


@router.get("/list", response_model=ApiResponse[list[CampaignItem]])
async def list_campaigns(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str = Query("active"),
):
    now = datetime.now(timezone.utc)
    campaigns_result = await db.execute(
        select(Campaign).where(
            Campaign.status == status,
            Campaign.deleted_at.is_(None),
            (Campaign.start_at.is_(None)) | (Campaign.start_at <= now),
            (Campaign.end_at.is_(None)) | (Campaign.end_at >= now),
        )
    )
    campaigns = campaigns_result.scalars().all()

    participations_result = await db.execute(
        select(CampaignParticipation).where(CampaignParticipation.customer_id == customer.id)
    )
    participations = {p.campaign_id: p for p in participations_result.scalars().all()}

    invitations_result = await db.execute(
        select(CampaignInvitation).where(CampaignInvitation.customer_id == customer.id)
    )
    invitations = {i.campaign_id: i for i in invitations_result.scalars().all()}

    def is_eligible(c: Campaign) -> bool:
        if c.eligibility_type == CampaignEligibilityType.ALL_CUSTOMERS:
            return True
        if c.eligibility_type == CampaignEligibilityType.ENROLLED_ONLY:
            return True
        if c.eligibility_type == CampaignEligibilityType.INVITE_ONLY:
            return c.id in invitations
        return False

    eligible = [c for c in campaigns if is_eligible(c)]

    return ApiResponse(
        data=[
            CampaignItem(
                campaign_id=c.id,
                name=c.name,
                description=c.description,
                type=c.type.value,
                eligibility_type=c.eligibility_type.value,
                status=c.status,
                reward_coins=c.reward_coins,
                tasks=c.tasks or [],
                start_at=c.start_at.isoformat() if c.start_at else None,
                end_at=c.end_at.isoformat() if c.end_at else None,
                participation_status=participations[c.id].status if c.id in participations else None,
                invitation_status=invitations[c.id].status if c.id in invitations else None,
            )
            for c in eligible
        ]
    )




@router.post("/{campaign_id}/enroll", response_model=ApiResponse[dict])
async def enroll_campaign(
    campaign_id: UUID,
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    if campaign.status != "active":
        raise HTTPException(409, detail={"code": "CONFLICT", "message": "Campaign is not active"})
    now = datetime.now(timezone.utc)
    if campaign.start_at and campaign.start_at > now:
        raise HTTPException(409, detail={"code": "CONFLICT", "message": "Campaign has not started"})
    if campaign.end_at and campaign.end_at < now:
        raise HTTPException(409, detail={"code": "CONFLICT", "message": "Campaign has ended"})
    if campaign.eligibility_type == CampaignEligibilityType.INVITE_ONLY:
        inv = await db.execute(
            select(CampaignInvitation).where(
                CampaignInvitation.campaign_id == campaign_id,
                CampaignInvitation.customer_id == customer.id,
            )
        )
        if not inv.scalar_one_or_none():
            raise HTTPException(403, detail={"code": "FORBIDDEN", "message": "Invitation required"})
    existing = await db.execute(
        select(CampaignParticipation).where(
            CampaignParticipation.campaign_id == campaign_id,
            CampaignParticipation.customer_id == customer.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, detail={"code": "CONFLICT", "message": "Already enrolled"})
    part = CampaignParticipation(
        customer_id=customer.id, campaign_id=campaign_id, enrolled_at=datetime.now(timezone.utc)
    )
    db.add(part)
    await db.flush()
    return ApiResponse(data={"participation_status": "enrolled"})


@router.get("/me/participations", response_model=ApiResponse[list[dict]])
async def my_participations(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(CampaignParticipation, Campaign)
        .join(Campaign, CampaignParticipation.campaign_id == Campaign.id)
        .where(CampaignParticipation.customer_id == customer.id)
    )
    return ApiResponse(
        data=[
            {
                "campaign_id": str(c.id),
                "campaign_name": c.name,
                "status": p.status,
                "enrolled_at": p.enrolled_at.isoformat(),
            }
            for p, c in result.all()
        ]
    )


@router.get("/{campaign_id}", response_model=ApiResponse[CampaignItem])
async def get_campaign(
    campaign_id: UUID,
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    participation = await db.scalar(
        select(CampaignParticipation).where(
            CampaignParticipation.campaign_id == campaign_id,
            CampaignParticipation.customer_id == customer.id,
        )
    )
    invitation = await db.scalar(
        select(CampaignInvitation).where(
            CampaignInvitation.campaign_id == campaign_id,
            CampaignInvitation.customer_id == customer.id,
        )
    )
    if c.status != "active":
        raise HTTPException(403, detail={"code": "FORBIDDEN", "message": "Campaign is not active"})
    if c.eligibility_type == CampaignEligibilityType.INVITE_ONLY and not invitation:
        raise HTTPException(403, detail={"code": "FORBIDDEN", "message": "Campaign invitation required"})
    return ApiResponse(
        data=CampaignItem(
            campaign_id=c.id,
            name=c.name,
            description=c.description,
            type=c.type.value,
            eligibility_type=c.eligibility_type.value,
            status=c.status,
            reward_coins=c.reward_coins,
            tasks=c.tasks or [],
            start_at=c.start_at.isoformat() if c.start_at else None,
            end_at=c.end_at.isoformat() if c.end_at else None,
            participation_status=participation.status if participation else None,
            invitation_status=invitation.status if invitation else None,
        )
    )
