from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_partner_api_key
from app.db.session import get_db
from app.models.customer import Customer
from app.schemas.common import ApiResponse
from app.services.booking_service import BookingService
from app.services.referral_service import ReferralService
from app.services.wallet_service import WalletService
from app.services.earning_service import EarningService

router = APIRouter()


class CustomerIdentity(BaseModel):
    customer_id: UUID | None = None
    phone: str | None = None
    email: str | None = None


class BookingConfirmedRequest(BaseModel):
    source_system: str
    source_booking_id: str
    customer_identity: CustomerIdentity
    confirmed_at: datetime
    booking_value_inr: Decimal = Field(gt=0)
    payload: dict = Field(default_factory=dict)


class CustomerSyncRequest(BaseModel):
    phone: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    external_customer_id: str | None = None


class ReferralValidateRequest(BaseModel):
    referral_code: str
    referred_phone: str | None = None
    referred_email: str | None = None


class RewardIssueRequest(BaseModel):
    customer_id: UUID
    amount: int = Field(gt=0)
    reason_code: str
    idempotency_key: str
    grant_source: str = "PARTNER_ISSUE"


async def resolve_customer(db: AsyncSession, identity: CustomerIdentity) -> Customer:
    if identity.customer_id:
        result = await db.execute(select(Customer).where(Customer.id == identity.customer_id))
        c = result.scalar_one_or_none()
        if c:
            return c
    if identity.phone:
        result = await db.execute(select(Customer).where(Customer.phone == identity.phone))
        c = result.scalar_one_or_none()
        if c:
            return c
    if identity.email:
        result = await db.execute(select(Customer).where(Customer.email == identity.email))
        c = result.scalar_one_or_none()
        if c:
            return c
    raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Customer not found"})


@router.post("/bookings/confirmed", response_model=ApiResponse[dict])
async def booking_confirmed(
    body: BookingConfirmedRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(verify_partner_api_key)],
):
    customer = await resolve_customer(db, body.customer_identity)
    svc = BookingService(db)
    event = await svc.confirm_booking(
        source_system=body.source_system,
        source_booking_id=body.source_booking_id,
        customer_id=customer.id,
        confirmed_at=body.confirmed_at,
        booking_value_inr=body.booking_value_inr,
        payload=body.payload,
    )
    return ApiResponse(
        data={
            "booking_event_id": str(event.id),
            "coins_awarded": event.coins_awarded,
            "customer_id": str(customer.id),
        }
    )


@router.post("/customers/sync", response_model=ApiResponse[dict])
async def customer_sync(
    body: CustomerSyncRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(verify_partner_api_key)],
):
    from app.models.customer import CustomerProfile
    from app.services.auth_service import AuthService

    customer = None
    if body.phone:
        result = await db.execute(select(Customer).where(Customer.phone == body.phone))
        customer = result.scalar_one_or_none()
    if not customer and body.email:
        result = await db.execute(select(Customer).where(Customer.email == body.email))
        customer = result.scalar_one_or_none()

    if not customer:
        auth = AuthService(db)
        if body.phone:
            customer = await auth.get_or_create_customer_by_phone(body.phone)
        else:
            customer = Customer(email=body.email)
            db.add(customer)
            await db.flush()
            db.add(CustomerProfile(customer_id=customer.id))
            wallet = WalletService(db)
            await wallet.ensure_wallet_balance(customer.id)

    if body.first_name:
        prof_result = await db.execute(select(CustomerProfile).where(CustomerProfile.customer_id == customer.id))
        profile = prof_result.scalar_one_or_none()
        if profile:
            profile.first_name = body.first_name
            profile.last_name = body.last_name

    referral = ReferralService(db)
    await referral.on_customer_registered(customer.id, body.phone, body.email)

    return ApiResponse(data={"customer_id": str(customer.id), "status": customer.status})


@router.post("/referrals/validate", response_model=ApiResponse[dict])
async def referral_validate(
    body: ReferralValidateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(verify_partner_api_key)],
):
    from app.models.referral import ReferralCode

    result = await db.execute(
        select(ReferralCode).where(ReferralCode.code == body.referral_code, ReferralCode.status == "active")
    )
    code = result.scalar_one_or_none()
    if not code:
        return ApiResponse(code="INVALID", message="Invalid referral code", data={"valid": False})

    if body.referred_phone:
        cust = await db.execute(select(Customer).where(Customer.phone == body.referred_phone))
        referred = cust.scalar_one_or_none()
        if referred and referred.id == code.customer_id:
            return ApiResponse(code="INVALID", message="Self referral", data={"valid": False})

    return ApiResponse(data={"valid": True, "referrer_customer_id": str(code.customer_id)})


@router.post("/rewards/issue", response_model=ApiResponse[dict])
async def partner_issue_coins(
    body: RewardIssueRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(verify_partner_api_key)],
):
    earning = EarningService(db)
    wallet = WalletService(db)
    _, grant = await wallet.issue_coins(
        customer_id=body.customer_id,
        amount=body.amount,
        grant_source=body.grant_source,
        reason_code=body.reason_code,
        idempotency_key=body.idempotency_key,
        reference_type="partner_issue",
    )
    balance = await wallet.ensure_wallet_balance(body.customer_id)
    from app.services.tier_service import TierService

    tier = TierService(db)
    await tier.evaluate_and_upgrade(body.customer_id, balance.lifetime_coins_earned, body.reason_code)
    return ApiResponse(data={"coin_grant_id": str(grant.id), "amount": body.amount})
