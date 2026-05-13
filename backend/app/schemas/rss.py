import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RssFeedCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=1, max_length=2000)
    feed_type: str = Field(default="rss", pattern=r"^(rss|atom)$")
    poll_interval: int = Field(default=60, ge=5, le=1440)
    filter_keywords: list[str] | None = None
    filter_authors: list[str] | None = None
    filter_categories: list[str] | None = None


class RssFeedUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    url: str | None = Field(default=None, min_length=1, max_length=2000)
    is_active: bool | None = None
    poll_interval: int | None = Field(default=None, ge=5, le=1440)
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
