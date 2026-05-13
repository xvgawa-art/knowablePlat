import uuid
from datetime import datetime

from pydantic import BaseModel


class GenerateRequest(BaseModel):
    kb_ids: list[str]
    topic: str


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
