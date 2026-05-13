import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wiki_page import WikiPage, WikiPageType
from app.repositories.base import BaseRepository


class WikiPageRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(WikiPage, session)

    async def create(self, **kwargs) -> WikiPage:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        combined = f"{instance.title or ''} {instance.content or ''}"
        instance.search_vector = func.to_tsvector("simple", combined)
        await self.session.flush()
        return instance

    async def update(self, instance: WikiPage, **kwargs) -> WikiPage:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.flush()
        if "title" in kwargs or "content" in kwargs:
            combined = f"{instance.title or ''} {instance.content or ''}"
            instance.search_vector = func.to_tsvector("simple", combined)
            await self.session.flush()
        return instance

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

    async def search(self, kb_id: uuid.UUID, query: str, offset: int = 0, limit: int = 20) -> list[WikiPage]:
        ts_query = func.plainto_tsquery("simple", query)
        result = await self.session.execute(
            select(WikiPage)
            .where(WikiPage.kb_id == kb_id, WikiPage.search_vector.op("@@")(ts_query))
            .order_by(func.ts_rank(WikiPage.search_vector, ts_query).desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
