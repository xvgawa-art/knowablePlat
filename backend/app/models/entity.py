import enum

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class EntityType(enum.StrEnum):
    person = "person"
    organization = "organization"
    tool = "tool"
    topic = "topic"
    event = "event"


class Entity(BaseModel):
    __tablename__ = "entities"

    kb_id: Mapped[str] = mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType), nullable=False)
    aliases: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
    wiki_page_id: Mapped[str | None] = mapped_column(ForeignKey("wiki_pages.id", ondelete="SET NULL"), nullable=True)
