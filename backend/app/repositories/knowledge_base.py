from sqlalchemy import select
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
