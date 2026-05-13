import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class FeedType(enum.StrEnum):
    rss = "rss"
    atom = "atom"


class FetchStatus(enum.StrEnum):
    success = "success"
    partial = "partial"
    failed = "failed"


class RssFeed(BaseModel):
    __tablename__ = "rss_feeds"

    kb_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    feed_type: Mapped[FeedType] = mapped_column(Enum(FeedType), default=FeedType.rss, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    poll_interval: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_fetch_status: Mapped[FetchStatus | None] = mapped_column(Enum(FetchStatus), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_fetched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    filter_keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    filter_authors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    filter_categories: Mapped[list | None] = mapped_column(JSON, nullable=True)
