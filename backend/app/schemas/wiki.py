import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WikiPageResponse(BaseModel):
    id: uuid.UUID
    kb_id: uuid.UUID
    slug: str
    title: str
    page_type: str
    content: str | None = None
    frontmatter: dict | None = None
    source_ids: list | None = None
    outgoing_links: list | None = None
    incoming_links: list | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class WikiPageListItem(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    page_type: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class WikiGraphData(BaseModel):
    nodes: list[dict]
    edges: list[dict]


class WikiQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class WikiQueryResponse(BaseModel):
    answer: str
    referenced_pages: list[str]


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=10, ge=1, le=50)


class WikiPageUpdate(BaseModel):
    content: str = Field(min_length=1)
    title: str | None = None
    outgoing_links: list[str] | None = None


class ActivityLogResponse(BaseModel):
    id: uuid.UUID
    kb_id: uuid.UUID
    action: str
    target: str
    details: dict | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
