from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.knowledge_base import KnowledgeBase
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.repositories.notification import NotificationRepository
from app.schemas.notification import NotificationListResponse, NotificationResponse

router = APIRouter(prefix="/api/kb/{kb_slug}/notifications", tags=["notifications"])


async def _get_kb(kb_slug: str, db: AsyncSession) -> KnowledgeBase:
    repo = KnowledgeBaseRepository(db)
    kb = await repo.get_by_slug(kb_slug)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
    return kb


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    kb_slug: str, unread: bool = False, offset: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)
):
    kb = await _get_kb(kb_slug, db)
    notif_repo = NotificationRepository(db)
    items = await notif_repo.list_by_kb(kb.id, unread_only=unread, offset=offset, limit=limit)
    all_unread = await notif_repo.list_by_kb(kb.id, unread_only=True, limit=1000)
    return NotificationListResponse(items=items, unread_count=len(all_unread))


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(kb_slug: str, notification_id: str, db: AsyncSession = Depends(get_db)):
    import uuid

    await _get_kb(kb_slug, db)
    notif_repo = NotificationRepository(db)
    try:
        nid = uuid.UUID(notification_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的通知 ID")
    notification = await notif_repo.get_by_id(nid)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")
    await notif_repo.mark_read(nid)
    return notification


@router.put("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(kb_slug: str, db: AsyncSession = Depends(get_db)):
    kb = await _get_kb(kb_slug, db)
    notif_repo = NotificationRepository(db)
    await notif_repo.mark_all_read(kb.id)
