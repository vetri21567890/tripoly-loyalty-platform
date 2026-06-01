from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_customer
from app.db.session import get_db
from app.models.customer import Customer
from app.models.wallet import CoinGrant, CoinTransaction
from app.schemas.common import ApiResponse
from app.schemas.wallet import CoinGrantResponse, CoinTransactionResponse, ExpiringSoonResponse, WalletBalanceResponse
from app.services.wallet_service import WalletService

router = APIRouter()


@router.get("/balance", response_model=ApiResponse[WalletBalanceResponse])
async def get_balance(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    wallet = WalletService(db)
    await wallet.expire_due_grants(customer.id)
    balance = await wallet.ensure_wallet_balance(customer.id)
    coins_per_rupee = await wallet.program_settings.coins_per_rupee()
    return ApiResponse(
        data=WalletBalanceResponse(
            available_coins=balance.available_coins,
            expired_coins=balance.expired_coins,
            lifetime_coins_earned=balance.lifetime_coins_earned,
            redeemed_coins_to_date=balance.redeemed_coins_to_date,
            approx_redemption_value_inr=balance.available_coins // coins_per_rupee if coins_per_rupee else 0,
            coins_per_rupee=coins_per_rupee,
            conversion_rule=f"{coins_per_rupee} Travel Coins = ₹1",
        )
    )


@router.get("/coin-grants", response_model=ApiResponse[list[CoinGrantResponse]])
async def list_coin_grants(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
):
    result = await db.execute(
        select(CoinGrant)
        .where(CoinGrant.customer_id == customer.id)
        .order_by(CoinGrant.created_at.desc())
        .limit(limit)
    )
    grants = result.scalars().all()
    return ApiResponse(
        data=[
            CoinGrantResponse(
                coin_grant_id=g.id,
                earned_date=g.earned_date,
                expiry_date=g.expiry_date,
                amount_remaining=g.amount_remaining,
                amount_total=g.amount_total,
                status=g.status.value,
                grant_source=g.grant_source,
            )
            for g in grants
        ]
    )


@router.get("/transactions", response_model=ApiResponse[list[CoinTransactionResponse]])
async def list_transactions(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
    type: str | None = Query(None, description="credit|debit|expire"),
):
    q = select(CoinTransaction).where(CoinTransaction.customer_id == customer.id)
    if type:
        q = q.where(CoinTransaction.direction == type)
    result = await db.execute(q.order_by(CoinTransaction.created_at.desc()).limit(limit))
    txs = result.scalars().all()
    return ApiResponse(
        data=[
            CoinTransactionResponse(
                transaction_id=t.id,
                direction=t.direction.value,
                amount=t.amount,
                earned_date=t.earned_date,
                expiry_date=t.expiry_date,
                reason_code=t.reason_code,
                created_at=t.created_at,
            )
            for t in txs
        ]
    )


@router.get("/expiring-soon", response_model=ApiResponse[ExpiringSoonResponse])
async def expiring_soon(
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
):
    wallet = WalletService(db)
    grants, total = await wallet.get_expiring_soon_grants(customer.id, within_days=days, limit=limit)
    return ApiResponse(
        data=ExpiringSoonResponse(
            days=days,
            total_amount_remaining=total,
            grants=[
                CoinGrantResponse(
                    coin_grant_id=g.id,
                    earned_date=g.earned_date,
                    expiry_date=g.expiry_date,
                    amount_remaining=g.amount_remaining,
                    amount_total=g.amount_total,
                    status=g.status.value,
                    grant_source=g.grant_source,
                )
                for g in grants
            ],
        )
    )
