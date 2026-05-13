import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: uuid.UUID
    kb_id: uuid.UUID
    source_id: uuid.UUID
    trigger_type: str
    title: str
    summary: str | None = None
    related_points: list | None = None
    is_read: bool = False
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    unread_count: int
