import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import Entity
from app.repositories.base import BaseRepository


class EntityRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(Entity, session)

    async def get_by_name(self, kb_id: uuid.UUID, name: str) -> Entity | None:
        result = await self.session.execute(select(Entity).where(Entity.kb_id == kb_id, Entity.name == name))
        return result.scalar_one_or_none()

    async def list_by_kb(self, kb_id: uuid.UUID, offset: int = 0, limit: int = 50) -> list[Entity]:
        result = await self.session.execute(select(Entity).where(Entity.kb_id == kb_id).offset(offset).limit(limit))
        return list(result.scalars().all())
