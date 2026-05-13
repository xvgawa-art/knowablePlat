from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseResponse, KnowledgeBaseUpdate

router = APIRouter(prefix="/api/knowledge-bases", tags=["knowledge-bases"])


def _repo(db: AsyncSession) -> KnowledgeBaseRepository:
    return KnowledgeBaseRepository(db)


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_kb(data: KnowledgeBaseCreate, db: AsyncSession = Depends(get_db)):
    repo = _repo(db)
    existing = await repo.get_by_slug(data.slug)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="slug 已被使用")
    return await repo.create(**data.model_dump())


@router.get("", response_model=list[KnowledgeBaseResponse])
async def list_kbs(offset: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    repo = _repo(db)
    return await repo.list_all(offset=offset, limit=limit)


@router.get("/{kb_slug}", response_model=KnowledgeBaseResponse)
async def get_kb(kb_slug: str, db: AsyncSession = Depends(get_db)):
    repo = _repo(db)
    kb = await repo.get_by_slug(kb_slug)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
    return kb


@router.put("/{kb_slug}", response_model=KnowledgeBaseResponse)
async def update_kb(kb_slug: str, data: KnowledgeBaseUpdate, db: AsyncSession = Depends(get_db)):
    repo = _repo(db)
    kb = await repo.get_by_slug(kb_slug)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
    if kb.is_system:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="系统内置知识库不可修改")
    update_data = data.model_dump(exclude_unset=True)
    return await repo.update(kb, **update_data)


@router.delete("/{kb_slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kb(kb_slug: str, db: AsyncSession = Depends(get_db)):
    repo = _repo(db)
    kb = await repo.get_by_slug(kb_slug)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
    if kb.is_system:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="系统内置知识库不可删除")
    await repo.delete(kb)
