import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import ActivityLog
from app.repositories.base import BaseRepository


class ActivityLogRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(ActivityLog, session)

    async def list_by_kb(self, kb_id: uuid.UUID, offset: int = 0, limit: int = 50) -> list[ActivityLog]:
        result = await self.session.execute(
            select(ActivityLog)
            .where(ActivityLog.kb_id == kb_id)
            .order_by(ActivityLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
