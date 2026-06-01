"""Reset the default admin account password.

Usage:
    python scripts/reset_admin_password.py

Optional environment variables:
    ADMIN_EMAIL
    ADMIN_PASSWORD
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.models.auth import AdminRole, AdminUser, AdminUserRole


DEFAULT_ADMIN_EMAIL = "admin@tripoly.app"
DEFAULT_ADMIN_PASSWORD = "admin123"


async def reset_admin_password() -> None:
    settings = get_settings()
    admin_email = os.getenv("ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL).strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as db:
        role = await db.scalar(select(AdminRole).where(func.lower(AdminRole.name) == "admin"))
        if not role:
            role = AdminRole(name="admin")
            db.add(role)
            await db.flush()
        else:
            role.name = "admin"
            await db.flush()

        admin = await db.scalar(select(AdminUser).where(func.lower(AdminUser.email) == admin_email))
        if not admin:
            admin = AdminUser(
                email=admin_email,
                password_hash=hash_password(admin_password),
                status="active",
            )
            db.add(admin)
            await db.flush()
        else:
            admin.email = admin_email
            admin.status = "active"
            admin.deleted_at = None
            admin.password_hash = hash_password(admin_password)
            await db.flush()

        link = await db.scalar(
            select(AdminUserRole).where(
                AdminUserRole.admin_user_id == admin.id,
                AdminUserRole.role_id == role.id,
            )
        )
        if not link:
            db.add(AdminUserRole(admin_user_id=admin.id, role_id=role.id))

        await db.commit()

    await engine.dispose()
    print(f"Admin password reset: {admin_email} / role=admin / status=active")


if __name__ == "__main__":
    asyncio.run(reset_admin_password())
