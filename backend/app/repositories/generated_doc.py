from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generated_doc import GeneratedDoc
from app.repositories.base import BaseRepository


class GeneratedDocRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(GeneratedDoc, session)

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[GeneratedDoc]:
        result = await self.session.execute(
            select(GeneratedDoc).order_by(GeneratedDoc.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self.session.scalar(select(func.count()).select_from(GeneratedDoc))
        return result or 0
