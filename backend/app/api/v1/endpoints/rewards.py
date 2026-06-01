from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_customer
from app.core.exceptions import AppException
from app.db.session import get_db
from app.models.customer import Customer
from app.models.rewards import RewardCatalog, RewardRedemption
from app.schemas.common import ApiResponse
from app.services.reward_service import RewardService
from app.services.program_settings_service import ProgramSettingsService

router = APIRouter()


class RewardCatalogItem(BaseModel):
    reward_catalog_id: UUID
    title: str
    reward_type: str
    cost_coins: int
    unlimited_inventory: bool
    inventory_remaining: int | None
    status: str
    approx_value_inr: int | None = None
    can_redeem: bool | None = None


class RedeemRequest(BaseModel):
    reward_catalog_id: UUID


class RedeemResponse(BaseModel):
    reward_redemption_id: UUID
    coins_spent: int
    redeemed_at: str
    voucher_code: str | None = None


@router.get("/catalog", response_model=ApiResponse[list[RewardCatalogItem]])
async def list_catalog(
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str = Query("active"),
    unlimited: bool | None = None,
):
    q = select(RewardCatalog).where(RewardCatalog.deleted_at.is_(None), RewardCatalog.status == status)
    if unlimited is not None:
        q = q.where(RewardCatalog.unlimited_inventory == unlimited)
    result = await db.execute(q.order_by(RewardCatalog.cost_coins))
    settings = ProgramSettingsService(db)
    coins_per_rupee = await settings.coins_per_rupee()
    return ApiResponse(
        data=[
            RewardCatalogItem(
                reward_catalog_id=r.id,
                title=r.title,
                reward_type=r.reward_type,
                cost_coins=r.cost_coins,
                unlimited_inventory=r.unlimited_inventory,
                inventory_remaining=r.inventory_remaining,
                status=r.status,
                approx_value_inr=r.cost_coins // coins_per_rupee if coins_per_rupee else None,
            )
            for r in result.scalars().all()
        ]
    )


@router.get("/catalog/{reward_catalog_id}", response_model=ApiResponse[RewardCatalogItem])
async def get_catalog_item(reward_catalog_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(RewardCatalog).where(RewardCatalog.id == reward_catalog_id, RewardCatalog.deleted_at.is_(None))
    )
    r = result.scalar_one_or_none()
    if not r:
        from fastapi import HTTPException

        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Reward not found"})
    settings = ProgramSettingsService(db)
    coins_per_rupee = await settings.coins_per_rupee()
    return ApiResponse(
        data=RewardCatalogItem(
            reward_catalog_id=r.id,
            title=r.title,
            reward_type=r.reward_type,
            cost_coins=r.cost_coins,
            unlimited_inventory=r.unlimited_inventory,
            inventory_remaining=r.inventory_remaining,
            status=r.status,
            approx_value_inr=r.cost_coins // coins_per_rupee if coins_per_rupee else None,
        )
    )


@router.post("/redemptions", response_model=ApiResponse[RedeemResponse])
async def redeem_reward(
    body: RedeemRequest,
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
):
    if not idempotency_key or len(idempotency_key) > 128:
        from fastapi import HTTPException

        raise HTTPException(400, detail={"code": "VALIDATION_ERROR", "message": "Idempotency-Key required"})
    try:
        svc = RewardService(db)
        redemption = await svc.redeem(customer.id, body.reward_catalog_id, idempotency_key)
    except AppException as e:
        from fastapi import HTTPException

        raise HTTPException(e.status_code, detail={"code": e.code, "message": e.message, "details": e.details})
    return ApiResponse(
        data=RedeemResponse(
            reward_redemption_id=redemption.id,
            coins_spent=redemption.coins_spent,
            redeemed_at=redemption.redeemed_at.isoformat(),
            voucher_code=(redemption.metadata_jsonb or {}).get("voucher_code"),
        )
    )


@router.get("/redemptions/history", response_model=ApiResponse[list[dict]])
async def redemption_history(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
):
    result = await db.execute(
        select(RewardRedemption, RewardCatalog)
        .join(RewardCatalog, RewardRedemption.reward_catalog_id == RewardCatalog.id)
        .where(RewardRedemption.customer_id == customer.id)
        .order_by(RewardRedemption.redeemed_at.desc())
        .limit(limit)
    )
    return ApiResponse(
        data=[
            {
                "reward_title": c.title,
                "reward_type": c.reward_type,
                "coins_spent": r.coins_spent,
                "status": r.status.value,
                "redeemed_at": r.redeemed_at.isoformat(),
                "voucher_code": (r.metadata_jsonb or {}).get("voucher_code"),
            }
            for r, c in result.all()
        ]
    )
