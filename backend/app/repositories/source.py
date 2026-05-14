import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source
from app.repositories.base import BaseRepository


class SourceRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(Source, session)

    async def list_by_kb(self, kb_id: uuid.UUID, offset: int = 0, limit: int = 50) -> list[Source]:
        result = await self.session.execute(select(Source).where(Source.kb_id == kb_id).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count_by_kb(self, kb_id: uuid.UUID) -> int:
        result = await self.session.scalar(select(func.count()).where(Source.kb_id == kb_id))
        return result or 0

    async def get_by_url(self, kb_id: uuid.UUID, url: str) -> Source | None:
        result = await self.session.execute(select(Source).where(Source.kb_id == kb_id, Source.url == url))
        return result.scalar_one_or_none()
