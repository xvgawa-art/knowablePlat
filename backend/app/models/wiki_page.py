import enum

from sqlalchemy import JSON, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class WikiPageType(enum.StrEnum):
    source = "source"
    entity = "entity"
    concept = "concept"
    comparison = "comparison"
    tool = "tool"
    tool_category = "tool_category"


class WikiPage(BaseModel):
    __tablename__ = "wiki_pages"

    kb_id: Mapped[str] = mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    slug: Mapped[str] = mapped_column(String(300), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    page_type: Mapped[WikiPageType] = mapped_column(Enum(WikiPageType), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    frontmatter: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    outgoing_links: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
    incoming_links: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
