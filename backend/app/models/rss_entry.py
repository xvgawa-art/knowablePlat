import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class EntryStatus(enum.StrEnum):
    new = "new"
    ingesting = "ingesting"
    completed = "completed"
    filtered = "filtered"
    failed = "failed"


class RssEntry(BaseModel):
    __tablename__ = "rss_entries"

    feed_id: Mapped[str] = mapped_column(ForeignKey("rss_feeds.id", ondelete="CASCADE"), nullable=False)
    kb_id: Mapped[str] = mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    guid: Mapped[str] = mapped_column(String(1000), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[EntryStatus] = mapped_column(Enum(EntryStatus), default=EntryStatus.new, nullable=False)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
