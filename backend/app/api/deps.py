from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.auth import AdminUser, AdminUserRole, AdminRole
from app.models.customer import Customer

security = HTTPBearer(auto_error=False)


async def get_current_customer(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Customer:
    if not credentials:
        raise HTTPException(status_code=401, detail={"code": "AUTH_REQUIRED", "message": "Authentication required"})
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=401, detail={"code": "AUTH_INVALID_TOKEN", "message": "Invalid token"})
    # Strictly enforce access-token + customer role.
    # This prevents admin tokens from being accepted by customer endpoints.
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail={"code": "AUTH_INVALID_TOKEN", "message": "Invalid token type"})
    if payload.get("role") != "customer":
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Customer access required"})
    customer_id = UUID(payload["sub"])
    result = await db.execute(
        select(Customer).where(Customer.id == customer_id, Customer.deleted_at.is_(None))
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=401, detail={"code": "AUTH_INVALID_TOKEN", "message": "Customer not found"})
    return customer


async def get_current_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdminUser:
    if not credentials:
        raise HTTPException(status_code=401, detail={"code": "AUTH_REQUIRED", "message": "Authentication required"})
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=401, detail={"code": "AUTH_INVALID_TOKEN", "message": "Invalid token"})
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Admin access required"})
    admin_id = UUID(payload["sub"])
    # Ensure admin is active and has an "admin" role assignment.
    result = await db.execute(
        select(AdminUser)
        .join(AdminUserRole, AdminUserRole.admin_user_id == AdminUser.id)
        .join(AdminRole, AdminRole.id == AdminUserRole.role_id)
        .where(AdminUser.id == admin_id, AdminUser.status == "active", AdminRole.name == "admin")
    )
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=401, detail={"code": "AUTH_INVALID_TOKEN", "message": "Admin not found"})
    return admin


async def verify_partner_api_key(x_api_key: Annotated[str | None, Header()] = None) -> str:
    settings = get_settings()
    if not x_api_key or x_api_key != settings.partner_api_key:
        raise HTTPException(status_code=401, detail={"code": "AUTH_REQUIRED", "message": "Invalid partner API key"})
    return x_api_key
