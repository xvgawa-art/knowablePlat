import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rss_feed import RssFeed
from app.repositories.base import BaseRepository


class RssFeedRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(RssFeed, session)

    async def list_by_kb(self, kb_id: uuid.UUID | str, offset: int = 0, limit: int = 50) -> list[RssFeed]:
        result = await self.session.execute(
            select(RssFeed).where(RssFeed.kb_id == str(kb_id)).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def list_active(self) -> list[RssFeed]:
        result = await self.session.execute(select(RssFeed).where(RssFeed.is_active == True))  # noqa: E712
        return list(result.scalars().all())
