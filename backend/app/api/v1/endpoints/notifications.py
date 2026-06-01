from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_customer
from app.db.session import get_db
from app.models.customer import Customer
from app.models.notification import InAppNotification
from app.schemas.common import ApiResponse
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, timezone

router = APIRouter()


class NotificationItem(BaseModel):
    id: UUID
    type: str
    title: str
    body: str | None
    read_at: str | None
    created_at: str


@router.get("/inbox", response_model=ApiResponse[list[NotificationItem]])
async def inbox(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
):
    result = await db.execute(
        select(InAppNotification)
        .where(InAppNotification.customer_id == customer.id)
        .order_by(InAppNotification.created_at.desc())
        .limit(limit)
    )
    return ApiResponse(
        data=[
            NotificationItem(
                id=n.id,
                type=n.type,
                title=n.title,
                body=n.body,
                read_at=n.read_at.isoformat() if n.read_at else None,
                created_at=n.created_at.isoformat(),
            )
            for n in result.scalars().all()
        ]
    )


@router.post("/{notification_id}/read", response_model=ApiResponse[dict])
async def mark_read(
    notification_id: UUID,
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(InAppNotification).where(
            InAppNotification.id == notification_id, InAppNotification.customer_id == customer.id
        )
    )
    n = result.scalar_one_or_none()
    if n:
        n.read_at = datetime.now(timezone.utc)
        await db.flush()
    return ApiResponse(data={"read_at": n.read_at.isoformat() if n and n.read_at else None})


@router.get("/unread-count", response_model=ApiResponse[dict])
async def unread_count(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    count = await db.scalar(
        select(func.count(InAppNotification.id)).where(
            InAppNotification.customer_id == customer.id, InAppNotification.read_at.is_(None)
        )
    )
    return ApiResponse(data={"unread_count": count or 0})
