import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.knowledge_base import KnowledgeBase
from app.models.source import SourceStatus
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.repositories.source import SourceRepository
from app.schemas.source import SourceCreate, SourceDetailResponse, SourceResponse
from app.services.fetcher import fetch_url

router = APIRouter(prefix="/api/kb/{kb_slug}/sources", tags=["sources"])


def _source_repo(db) -> SourceRepository:
    return SourceRepository(db)


async def _get_kb(kb_slug: str, db: AsyncSession) -> KnowledgeBase:
    repo = KnowledgeBaseRepository(db)
    kb = await repo.get_by_slug(kb_slug)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
    return kb


async def _ingest_source(source_id: uuid.UUID, kb_slug: str) -> None:
    """Background task: fetch URL and store raw content."""
    from app.database import async_sessionmaker

    async with async_sessionmaker() as session:
        async with session.begin():
            repo = SourceRepository(session)
            source = await repo.get_by_id(source_id)
            if source is None:
                return
            try:
                content = await fetch_url(source.url)
                source.raw_content = content
                source.status = SourceStatus.completed
            except Exception:
                source.status = SourceStatus.failed


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    kb_slug: str, data: SourceCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    kb = await _get_kb(kb_slug, db)
    existing = await _source_repo(db).get_by_url(kb.id, data.url)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该 URL 已存在于当前知识库")

    source = await _source_repo(db).create(kb_id=kb.id, url=data.url, status=SourceStatus.processing)
    background_tasks.add_task(_ingest_source, source.id, kb_slug)
    return source


@router.get("", response_model=list[SourceResponse])
async def list_sources(kb_slug: str, offset: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    kb = await _get_kb(kb_slug, db)
    return await _source_repo(db).list_by_kb(kb.id, offset=offset, limit=limit)


@router.get("/{source_id}", response_model=SourceDetailResponse)
async def get_source(kb_slug: str, source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    kb = await _get_kb(kb_slug, db)
    source = await _source_repo(db).get_by_id(source_id)
    if source is None or source.kb_id != kb.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="来源不存在")
    return source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(kb_slug: str, source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    kb = await _get_kb(kb_slug, db)
    source = await _source_repo(db).get_by_id(source_id)
    if source is None or source.kb_id != kb.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="来源不存在")
    await _source_repo(db).delete(source)
