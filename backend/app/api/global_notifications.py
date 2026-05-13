import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.repositories.notification import NotificationRepository
from app.schemas.notification import NotificationListResponse, NotificationResponse

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


async def _enrich_with_kb_slug(items: list, db: AsyncSession) -> list[dict]:
    kb_repo = KnowledgeBaseRepository(db)
    kb_slug_cache: dict[str, str] = {}
    result = []
    for item in items:
        kb_id_str = str(item.kb_id)
        if kb_id_str not in kb_slug_cache:
            kb = await kb_repo.get_by_id(item.kb_id)
            kb_slug_cache[kb_id_str] = kb.slug if kb else ""
        data = NotificationResponse.model_validate(item).model_dump()
        data["kb_slug"] = kb_slug_cache.get(kb_id_str, "")
        result.append(data)
    return result


@router.get("", response_model=NotificationListResponse)
async def list_all_notifications(
    unread: bool = False,
    kb_id: uuid.UUID | None = None,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    notif_repo = NotificationRepository(db)
    if kb_id:
        items = await notif_repo.list_by_kb(kb_id, unread_only=unread, offset=offset, limit=limit)
    else:
        items = await notif_repo.list_all(unread_only=unread, offset=offset, limit=limit)
    unread_count = await notif_repo.count_unread(kb_id=kb_id)
    enriched = await _enrich_with_kb_slug(items, db)
    return NotificationListResponse(items=enriched, unread_count=unread_count)


@router.get("/unread-count")
async def get_unread_count(kb_id: uuid.UUID | None = None, db: AsyncSession = Depends(get_db)):
    notif_repo = NotificationRepository(db)
    count = await notif_repo.count_unread(kb_id=kb_id)
    return {"unread_count": count}


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(notification_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    notif_repo = NotificationRepository(db)
    notification = await notif_repo.get_by_id(notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")
    enriched = (await _enrich_with_kb_slug([notification], db))[0]
    return enriched


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(notification_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    notif_repo = NotificationRepository(db)
    notification = await notif_repo.get_by_id(notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")
    await notif_repo.mark_read(notification_id)
    enriched = (await _enrich_with_kb_slug([notification], db))[0]
    return enriched


@router.put("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(kb_id: uuid.UUID | None = None, db: AsyncSession = Depends(get_db)):
    notif_repo = NotificationRepository(db)
    await notif_repo.mark_all_read(kb_id)
