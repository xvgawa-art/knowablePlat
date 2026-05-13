import enum

from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class KbType(enum.StrEnum):
    knowledge = "knowledge"
    tool_arsenal = "tool_arsenal"


class KnowledgeBase(BaseModel):
    __tablename__ = "knowledge_bases"

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    kb_type: Mapped[KbType] = mapped_column(Enum(KbType), default=KbType.knowledge, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wiki_page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
