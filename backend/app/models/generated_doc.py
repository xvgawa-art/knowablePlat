import enum

from sqlalchemy import JSON, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class DocStatus(enum.StrEnum):
    generating = "generating"
    completed = "completed"
    failed = "failed"


class GeneratedDoc(BaseModel):
    __tablename__ = "generated_docs"

    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    kb_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    referenced_page_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[DocStatus] = mapped_column(Enum(DocStatus), default=DocStatus.generating, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_usage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
