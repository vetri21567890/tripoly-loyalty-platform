from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_customer
from app.core.exceptions import AppException
from app.db.session import get_db
from app.models.customer import Customer
from app.models.enums import UgcType
from app.models.ugc import UgcAttempt, UgcThread
from app.schemas.common import ApiResponse
from app.services.ugc_service import UgcService

router = APIRouter()


class UgcInitRequest(BaseModel):
    ugc_type: UgcType
    ugc_thread_id: UUID | None = None
    destination: str | None = None


class UgcCompleteRequest(BaseModel):
    ugc_thread_id: UUID
    media_object_key: str
    content_metadata: dict = Field(default_factory=dict)


@router.post("/upload/init", response_model=ApiResponse[dict])
async def init_upload(
    body: UgcInitRequest,
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = UgcService(db)
        data = await svc.init_upload(customer.id, body.ugc_type, body.destination, body.ugc_thread_id)
    except AppException as e:
        from fastapi import HTTPException

        raise HTTPException(e.status_code, detail={"code": e.code, "message": e.message})
    return ApiResponse(data=data)


@router.post("/upload/complete", response_model=ApiResponse[dict])
async def complete_upload(
    body: UgcCompleteRequest,
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = UgcService(db)
        attempt = await svc.complete_upload(
            customer.id, body.ugc_thread_id, body.media_object_key, body.content_metadata
        )
    except AppException as e:
        from fastapi import HTTPException

        raise HTTPException(e.status_code, detail={"code": e.code, "message": e.message})
    return ApiResponse(data={"ugc_attempt_id": str(attempt.id), "status": attempt.status.value})


@router.get("/my-posts", response_model=ApiResponse[list[dict]])
async def my_posts(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
):
    result = await db.execute(
        select(UgcAttempt, UgcThread)
        .join(UgcThread, UgcAttempt.ugc_thread_id == UgcThread.id)
        .where(UgcThread.customer_id == customer.id)
        .order_by(UgcAttempt.created_at.desc())
        .limit(limit)
    )
    return ApiResponse(
        data=[
            {
                "ugc_thread_id": str(t.id),
                "ugc_attempt_id": str(a.id),
                "ugc_type": t.ugc_type.value,
                "status": a.status.value,
                "rejection_reason": a.rejection_reason,
                "created_at": a.created_at.isoformat(),
            }
            for a, t in result.all()
        ]
    )
