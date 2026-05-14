import uuid
from typing import TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository:
    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: uuid.UUID) -> ModelType | None:
        return await self.session.get(self.model, id)

    async def get_by_slug(self, slug: str) -> ModelType | None:
        result = await self.session.execute(select(self.model).where(self.model.slug == slug))
        return result.scalar_one_or_none()

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[ModelType]:
        result = await self.session.execute(select(self.model).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self.session.scalar(select(func.count()).select_from(self.model))
        return result or 0

    async def delete_many(self, ids: list[uuid.UUID]) -> int:
        result = await self.session.execute(delete(self.model).where(self.model.id.in_(ids)))
        await self.session.flush()
        return result.rowcount

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, instance: ModelType, **kwargs) -> ModelType:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def delete(self, instance: ModelType) -> None:
        await self.session.delete(instance)
        await self.session.flush()
