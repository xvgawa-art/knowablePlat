import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.source import SourceStatus


class SourceCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2000)


class BatchSourceCreate(BaseModel):
    urls: list[str] = Field(min_length=1, max_length=50)


class SourceResponse(BaseModel):
    id: uuid.UUID
    kb_id: uuid.UUID
    url: str
    title: str | None
    status: SourceStatus
    token_usage: int
    fetched_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceDetailResponse(SourceResponse):
    raw_content: str | None
