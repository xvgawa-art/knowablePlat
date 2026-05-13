import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(Notification, session)

    async def list_by_kb(
        self, kb_id: uuid.UUID, unread_only: bool = False, offset: int = 0, limit: int = 50
    ) -> list[Notification]:
        query = select(Notification).where(Notification.kb_id == kb_id).order_by(Notification.created_at.desc())
        if unread_only:
            query = query.where(Notification.is_read == False)  # noqa: E712
        result = await self.session.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all())

    async def mark_read(self, notification_id: uuid.UUID) -> None:
        await self.session.execute(update(Notification).where(Notification.id == notification_id).values(is_read=True))
        await self.session.flush()

    async def list_all(self, unread_only: bool = False, offset: int = 0, limit: int = 50) -> list[Notification]:
        query = select(Notification).order_by(Notification.created_at.desc())
        if unread_only:
            query = query.where(Notification.is_read == False)  # noqa: E712
        result = await self.session.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count_unread(self, kb_id: uuid.UUID | None = None) -> int:
        from sqlalchemy import func

        query = select(func.count()).where(Notification.is_read == False)  # noqa: E712
        if kb_id:
            query = query.where(Notification.kb_id == kb_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def mark_all_read(self, kb_id: uuid.UUID) -> None:
        await self.session.execute(
            update(Notification).where(Notification.kb_id == kb_id, Notification.is_read == False).values(is_read=True)  # noqa: E712
        )
        await self.session.flush()
