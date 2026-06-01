from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_customer
from app.db.session import get_db
from app.models.customer import Customer
from app.models.mission import CustomerMissionCompletion, Mission, MissionRewardRule
from app.schemas.common import ApiResponse
from pydantic import BaseModel

router = APIRouter()


class MissionAvailable(BaseModel):
    mission_code: str
    title: str
    coins_awarded: int
    is_one_time: bool


class MissionProgress(BaseModel):
    mission_code: str
    title: str
    status: str
    coins_awarded: int | None
    completed_at: str | None


@router.get("/available", response_model=ApiResponse[list[MissionAvailable]])
async def available_missions(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Mission).where(Mission.status == "active", Mission.deleted_at.is_(None)))
    missions = result.scalars().all()
    data = []
    for m in missions:
        rule_result = await db.execute(
            select(MissionRewardRule)
            .where(MissionRewardRule.mission_id == m.id, MissionRewardRule.status == "active")
            .limit(1)
        )
        rule = rule_result.scalar_one_or_none()
        data.append(
            MissionAvailable(
                mission_code=m.code,
                title=m.title,
                coins_awarded=rule.coins_awarded if rule else 0,
                is_one_time=m.is_one_time,
            )
        )
    return ApiResponse(data=data)


@router.get("/progress", response_model=ApiResponse[list[MissionProgress]])
async def mission_progress(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(CustomerMissionCompletion, Mission)
        .join(Mission, CustomerMissionCompletion.mission_id == Mission.id)
        .where(CustomerMissionCompletion.customer_id == customer.id)
    )
    return ApiResponse(
        data=[
            MissionProgress(
                mission_code=m.code,
                title=m.title,
                status=c.status.value,
                coins_awarded=c.coins_awarded,
                completed_at=c.completed_at.isoformat() if c.completed_at else None,
            )
            for c, m in result.all()
        ]
    )
