import enum

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ActionEnum(enum.StrEnum):
    ingest = "ingest"
    query = "query"
    lint = "lint"
    update = "update"


class ActivityLog(BaseModel):
    __tablename__ = "activity_log"

    kb_id: Mapped[str] = mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[ActionEnum] = mapped_column(Enum(ActionEnum), nullable=False)
    target: Mapped[str] = mapped_column(String(500), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
