import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.knowledge_base import KbType


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = Field(default=None, max_length=1000)
    icon: str | None = Field(default=None, max_length=100)
    color: str | None = Field(default=None, max_length=20)
    is_public: bool = False


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    icon: str | None = Field(default=None, max_length=100)
    color: str | None = Field(default=None, max_length=20)
    is_public: bool | None = None


class KnowledgeBaseResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    kb_type: KbType
    is_system: bool
    icon: str | None
    color: str | None
    is_public: bool
    source_count: int
    wiki_page_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
