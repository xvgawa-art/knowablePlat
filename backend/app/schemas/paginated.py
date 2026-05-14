from pydantic import BaseModel, Field


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int


class BatchDeleteRequest(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=100)
