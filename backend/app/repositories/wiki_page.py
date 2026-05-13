import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wiki_page import WikiPage, WikiPageType
from app.repositories.base import BaseRepository


class WikiPageRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(WikiPage, session)

    async def get_by_slug(self, kb_id: uuid.UUID, slug: str) -> WikiPage | None:
        result = await self.session.execute(select(WikiPage).where(WikiPage.kb_id == kb_id, WikiPage.slug == slug))
        return result.scalar_one_or_none()

    async def list_by_kb(
        self, kb_id: uuid.UUID, page_type: WikiPageType | None = None, offset: int = 0, limit: int = 50
    ) -> list[WikiPage]:
        query = select(WikiPage).where(WikiPage.kb_id == kb_id)
        if page_type:
            query = query.where(WikiPage.page_type == page_type)
        result = await self.session.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all())

    async def list_by_source(self, kb_id: uuid.UUID, source_id: uuid.UUID) -> list[WikiPage]:
        result = await self.session.execute(
            select(WikiPage).where(WikiPage.kb_id == kb_id, WikiPage.source_ids.contains([str(source_id)]))
        )
        return list(result.scalars().all())
