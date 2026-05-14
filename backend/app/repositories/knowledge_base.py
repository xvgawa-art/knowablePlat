import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KbType, KnowledgeBase
from app.repositories.base import BaseRepository


class KnowledgeBaseRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(KnowledgeBase, session)

    async def get_by_slug(self, slug: str) -> KnowledgeBase | None:
        result = await self.session.execute(select(KnowledgeBase).where(KnowledgeBase.slug == slug))
        return result.scalar_one_or_none()

    async def get_tool_arsenal(self) -> KnowledgeBase | None:
        result = await self.session.execute(
            select(KnowledgeBase).where(KnowledgeBase.kb_type == KbType.tool_arsenal).limit(1)
        )
        return result.scalar_one_or_none()

    async def ensure_tool_arsenal(self) -> KnowledgeBase:
        existing = await self.get_tool_arsenal()
        if existing:
            return existing
        return await self.create(
            name="工具装备",
            slug="tool-arsenal",
            description="系统内置工具知识库，存放各类安全工具的简介、用途和链接",
            kb_type=KbType.tool_arsenal,
            is_system=True,
        )

    async def list_by_user(self, user_id: str | uuid.UUID, offset: int = 0, limit: int = 50) -> list[KnowledgeBase]:
        from sqlalchemy import or_

        result = await self.session.execute(
            select(KnowledgeBase)
            .where(
                or_(
                    KnowledgeBase.user_id == user_id,
                    KnowledgeBase.is_public,
                    KnowledgeBase.is_system,
                )
            )
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: str | uuid.UUID) -> int:
        from sqlalchemy import func, or_

        result = await self.session.scalar(
            select(func.count())
            .select_from(KnowledgeBase)
            .where(
                or_(
                    KnowledgeBase.user_id == user_id,
                    KnowledgeBase.is_public,
                    KnowledgeBase.is_system,
                )
            )
        )
        return result or 0

    async def refresh_counts(self, kb_id: str) -> None:
        """Update denormalized source_count and wiki_page_count from actual data."""
        from app.models.source import Source
        from app.models.wiki_page import WikiPage

        source_count = await self.session.scalar(select(func.count()).select_from(Source).where(Source.kb_id == kb_id))
        wiki_count = await self.session.scalar(
            select(func.count()).select_from(WikiPage).where(WikiPage.kb_id == kb_id)
        )
        kb = await self.get_by_id(kb_id)
        if kb:
            kb.source_count = source_count or 0
            kb.wiki_page_count = wiki_count or 0
