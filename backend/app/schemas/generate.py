import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    kb_ids: list[str] = Field(min_length=1)
    topic: str = Field(min_length=1, max_length=2000)


class GenerateResponse(BaseModel):
    id: uuid.UUID
    title: str
    topic: str
    content: str | None = None
    kb_ids: list[str] | None = None
    status: str
    word_count: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class GenerateListItem(BaseModel):
    id: uuid.UUID
    title: str
    topic: str
    status: str
    word_count: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
