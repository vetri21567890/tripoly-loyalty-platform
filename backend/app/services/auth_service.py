from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, RateLimitedError, UnauthorizedError, ValidationError
from app.core.security import (
    create_access_token,
    generate_otp,
    generate_refresh_token,
    hash_otp,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.auth import OtpSession, RefreshToken
from app.models.customer import Customer, CustomerProfile
from app.models.referral import ReferralCode
from app.services.wallet_service import WalletService


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def get_or_create_customer_by_phone(self, phone: str) -> Customer:
        result = await self.db.execute(
            select(Customer).where(Customer.phone == phone, Customer.deleted_at.is_(None))
        )
        customer = result.scalar_one_or_none()
        if customer:
            return customer
        customer = Customer(phone=phone)
        self.db.add(customer)
        await self.db.flush()
        self.db.add(CustomerProfile(customer_id=customer.id))
        wallet = WalletService(self.db)
        await wallet.ensure_wallet_balance(customer.id)
        code = f"TRIP{str(customer.id).replace('-', '')[:8].upper()}"
        self.db.add(ReferralCode(customer_id=customer.id, code=code))
        await self.db.flush()
        return customer

    async def signup_with_email(
        self, email: str, password: str, first_name: str | None = None, last_name: str | None = None
    ) -> tuple[str, str, Customer]:
        existing = await self.db.execute(
            select(Customer).where(Customer.email == email, Customer.deleted_at.is_(None))
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Email already registered", code="EMAIL_ALREADY_EXISTS")

        customer = Customer(email=email, password_hash=hash_password(password), status="active")
        self.db.add(customer)
        await self.db.flush()

        self.db.add(CustomerProfile(customer_id=customer.id, first_name=first_name, last_name=last_name))
        wallet = WalletService(self.db)
        await wallet.ensure_wallet_balance(customer.id)
        code = f"TRIP{str(customer.id).replace('-', '')[:8].upper()}"
        self.db.add(ReferralCode(customer_id=customer.id, code=code))
        await self.db.flush()

        access = create_access_token(customer.id, role="customer")
        refresh_raw = generate_refresh_token()
        self.db.add(
            RefreshToken(
                customer_id=customer.id,
                token_hash=hash_token(refresh_raw),
                expires_at=datetime.now(timezone.utc) + timedelta(days=self.settings.refresh_token_expire_days),
            )
        )
        await self.db.flush()
        return access, refresh_raw, customer

    async def signin_with_email(self, email: str, password: str) -> tuple[str, str, Customer]:
        result = await self.db.execute(
            select(Customer).where(Customer.email == email, Customer.deleted_at.is_(None))
        )
        customer = result.scalar_one_or_none()
        if not customer or not customer.password_hash:
            raise UnauthorizedError("Invalid email or password")
        if not verify_password(password, customer.password_hash):
            raise UnauthorizedError("Invalid email or password")

        access = create_access_token(customer.id, role="customer")
        refresh_raw = generate_refresh_token()
        self.db.add(
            RefreshToken(
                customer_id=customer.id,
                token_hash=hash_token(refresh_raw),
                expires_at=datetime.now(timezone.utc) + timedelta(days=self.settings.refresh_token_expire_days),
            )
        )
        await self.db.flush()
        return access, refresh_raw, customer

    async def send_otp(self, phone: str) -> UUID:
        customer = await self.get_or_create_customer_by_phone(phone)
        settings = self.settings
        otp = generate_otp()
        session = OtpSession(
            customer_id=customer.id,
            channel="phone",
            code_hash=hash_otp(otp),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expire_minutes),
        )
        self.db.add(session)
        await self.db.flush()
        # In production: enqueue SMS via worker. Dev: log OTP.
        import logging

        logging.getLogger(__name__).info("OTP for %s: %s (dev only)", phone, otp)
        return session.id

    async def verify_otp(self, phone: str, otp: str) -> tuple[str, str, Customer]:
        result = await self.db.execute(
            select(Customer).where(Customer.phone == phone, Customer.deleted_at.is_(None))
        )
        customer = result.scalar_one_or_none()
        if not customer:
            raise UnauthorizedError("Invalid credentials")

        session_result = await self.db.execute(
            select(OtpSession)
            .where(OtpSession.customer_id == customer.id)
            .order_by(OtpSession.created_at.desc())
            .limit(1)
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise UnauthorizedError("OTP session not found")
        if session.locked_until and session.locked_until > datetime.now(timezone.utc):
            raise RateLimitedError("Account temporarily locked")
        if session.expires_at < datetime.now(timezone.utc):
            raise UnauthorizedError("OTP expired", details={"code": "AUTH_INVALID_OTP"})
        if session.code_hash != hash_otp(otp):
            session.attempt_count += 1
            if session.attempt_count >= self.settings.otp_max_attempts:
                session.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=self.settings.otp_lockout_minutes
                )
            await self.db.flush()
            raise UnauthorizedError("Invalid OTP", details={"code": "AUTH_INVALID_OTP"})

        access = create_access_token(customer.id, role="customer")
        refresh_raw = generate_refresh_token()
        refresh = RefreshToken(
            customer_id=customer.id,
            token_hash=hash_token(refresh_raw),
            expires_at=datetime.now(timezone.utc) + timedelta(days=self.settings.refresh_token_expire_days),
        )
        self.db.add(refresh)
        await self.db.flush()
        return access, refresh_raw, customer

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        token_hash = hash_token(refresh_token)
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
        )
        stored = result.scalar_one_or_none()
        if not stored or stored.expires_at < datetime.now(timezone.utc):
            raise UnauthorizedError("Refresh token invalid or expired", details={"code": "AUTH_REFRESH_REVOKED"})

        stored.revoked_at = datetime.now(timezone.utc)
        stored.revoked_reason = "rotation"
        access = create_access_token(stored.customer_id, role="customer")
        new_raw = generate_refresh_token()
        self.db.add(
            RefreshToken(
                customer_id=stored.customer_id,
                token_hash=hash_token(new_raw),
                expires_at=datetime.now(timezone.utc) + timedelta(days=self.settings.refresh_token_expire_days),
            )
        )
        await self.db.flush()
        return access, new_raw

    async def logout(self, customer_id: UUID, refresh_token: str | None) -> None:
        if refresh_token:
            token_hash = hash_token(refresh_token)
            result = await self.db.execute(
                select(RefreshToken).where(
                    RefreshToken.customer_id == customer_id,
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.revoked_at.is_(None),
                )
            )
            stored = result.scalar_one_or_none()
            if stored:
                stored.revoked_at = datetime.now(timezone.utc)
                stored.revoked_reason = "logout"
