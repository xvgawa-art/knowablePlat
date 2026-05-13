import uuid
from datetime import datetime

from pydantic import BaseModel


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
    question: str


class WikiQueryResponse(BaseModel):
    answer: str
    referenced_pages: list[str]


class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 10


class ActivityLogResponse(BaseModel):
    id: uuid.UUID
    kb_id: uuid.UUID
    action: str
    target: str
    details: dict | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
