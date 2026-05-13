import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.notification import NotificationRepository
from app.schemas.notification import NotificationListResponse, NotificationResponse

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_all_notifications(
    unread: bool = False, offset: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)
):
    notif_repo = NotificationRepository(db)
    items = await notif_repo.list_all(unread_only=unread, offset=offset, limit=limit)
    unread_count = await notif_repo.count_unread()
    return NotificationListResponse(items=items, unread_count=unread_count)


@router.get("/unread-count")
async def get_unread_count(db: AsyncSession = Depends(get_db)):
    notif_repo = NotificationRepository(db)
    count = await notif_repo.count_unread()
    return {"unread_count": count}


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(notification_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    notif_repo = NotificationRepository(db)
    notification = await notif_repo.get_by_id(notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")
    return notification


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(notification_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    notif_repo = NotificationRepository(db)
    notification = await notif_repo.get_by_id(notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")
    await notif_repo.mark_read(notification_id)
    return notification


@router.put("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(db: AsyncSession = Depends(get_db)):
    notif_repo = NotificationRepository(db)
    items = await notif_repo.list_all(unread_only=True, limit=10000)
    for item in items:
        await notif_repo.mark_read(item.id)
