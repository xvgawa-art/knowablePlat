import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rss_entry import RssEntry
from app.repositories.base import BaseRepository


class RssEntryRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(RssEntry, session)

    async def list_by_feed(
        self, feed_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> list[RssEntry]:
        result = await self.session.execute(
            select(RssEntry)
            .where(RssEntry.feed_id == feed_id)
            .order_by(RssEntry.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_guid(self, feed_id: uuid.UUID, guid: str) -> RssEntry | None:
        result = await self.session.execute(
            select(RssEntry).where(RssEntry.feed_id == feed_id, RssEntry.guid == guid)
        )
        return result.scalar_one_or_none()
