"""Base repository pattern - extend per aggregate as needed."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, model, entity_id: UUID):
        result = await self.db.execute(select(model).where(model.id == entity_id))
        return result.scalar_one_or_none()
