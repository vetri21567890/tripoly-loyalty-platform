from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_customer
from app.core.config import get_settings
from app.db.session import get_db
from app.models.customer import Customer
from app.schemas.auth import (
    CustomerMeResponse,
    OtpSendRequest,
    OtpSendResponse,
    OtpVerifyRequest,
    RefreshTokenRequest,
    SigninRequest,
    SignupRequest,
    TokenResponse,
)
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/signup", response_model=ApiResponse[TokenResponse])
async def signup(body: SignupRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    svc = AuthService(db)
    access, refresh, customer = await svc.signup_with_email(
        email=body.email,
        password=body.password,
        first_name=body.first_name,
        last_name=body.last_name,
    )
    from app.services.referral_service import ReferralService

    referral_svc = ReferralService(db)
    await referral_svc.on_customer_registered(customer.id, customer.phone, customer.email)
    settings = get_settings()
    return ApiResponse(
        data=TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in_seconds=settings.access_token_expire_minutes * 60,
        )
    )


@router.post("/signin", response_model=ApiResponse[TokenResponse])
async def signin(body: SigninRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    svc = AuthService(db)
    access, refresh, _ = await svc.signin_with_email(email=body.email, password=body.password)
    settings = get_settings()
    return ApiResponse(
        data=TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in_seconds=settings.access_token_expire_minutes * 60,
        )
    )


@router.post("/otp/send", response_model=ApiResponse[OtpSendResponse])
async def send_otp(body: OtpSendRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    svc = AuthService(db)
    request_id = await svc.send_otp(body.phone)
    return ApiResponse(data=OtpSendResponse(request_id=request_id))


@router.post("/otp/verify", response_model=ApiResponse[TokenResponse])
async def verify_otp(body: OtpVerifyRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    svc = AuthService(db)
    access, refresh, customer = await svc.verify_otp(body.phone, body.otp)
    from app.services.referral_service import ReferralService

    referral_svc = ReferralService(db)
    await referral_svc.on_customer_registered(customer.id, customer.phone, customer.email)
    settings = get_settings()
    return ApiResponse(
        data=TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in_seconds=settings.access_token_expire_minutes * 60,
        )
    )


@router.post("/token/refresh", response_model=ApiResponse[TokenResponse])
async def refresh_token(body: RefreshTokenRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    if not body.refresh_token:
        from fastapi import HTTPException

        raise HTTPException(400, detail={"code": "VALIDATION_ERROR", "message": "refresh_token required"})
    svc = AuthService(db)
    access, refresh = await svc.refresh_tokens(body.refresh_token)
    settings = get_settings()
    return ApiResponse(
        data=TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in_seconds=settings.access_token_expire_minutes * 60,
        )
    )


@router.post("/logout", response_model=ApiResponse[dict])
async def logout(
    body: RefreshTokenRequest,
    customer: Annotated[Customer, Depends(get_current_customer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = AuthService(db)
    await svc.logout(customer.id, body.refresh_token)
    return ApiResponse(data={"revoked": True})


@router.get("/me", response_model=ApiResponse[CustomerMeResponse])
async def me(customer: Annotated[Customer, Depends(get_current_customer)]):
    return ApiResponse(
        data=CustomerMeResponse(
            id=customer.id, phone=customer.phone, email=customer.email, status=customer.status
        )
    )
