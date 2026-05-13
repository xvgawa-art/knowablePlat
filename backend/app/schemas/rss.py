import uuid
from datetime import datetime

from pydantic import BaseModel


class RssFeedCreate(BaseModel):
    name: str
    url: str
    feed_type: str = "rss"
    poll_interval: int = 60
    filter_keywords: list[str] | None = None
    filter_authors: list[str] | None = None
    filter_categories: list[str] | None = None


class RssFeedUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    is_active: bool | None = None
    poll_interval: int | None = None
    filter_keywords: list[str] | None = None
    filter_authors: list[str] | None = None
    filter_categories: list[str] | None = None


class RssFeedResponse(BaseModel):
    id: uuid.UUID
    kb_id: uuid.UUID
    name: str
    url: str
    feed_type: str
    is_active: bool
    poll_interval: int
    last_fetched_at: datetime | None = None
    last_fetch_status: str | None = None
    last_error: str | None = None
    total_fetched: int
    filter_keywords: list[str] | None = None
    filter_authors: list[str] | None = None
    filter_categories: list[str] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RssEntryResponse(BaseModel):
    id: uuid.UUID
    feed_id: uuid.UUID
    kb_id: uuid.UUID
    guid: str
    url: str
    title: str | None = None
    published_at: datetime | None = None
    source_id: uuid.UUID | None = None
    status: str
    fetched_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
