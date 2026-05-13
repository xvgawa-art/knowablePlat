import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.knowledge_base import KnowledgeBase
from app.models.source import SourceStatus
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.repositories.source import SourceRepository
from app.schemas.source import BatchSourceCreate, SourceCreate, SourceDetailResponse, SourceResponse
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
    """Background task: fetch URL content, then run appropriate ingest pipeline."""
    from app.database import async_sessionmaker
    from app.models.knowledge_base import KbType
    from app.services.ingest import run_ingest_pipeline
    from app.services.tool_arsenal import run_tool_arsenal_pipeline

    # Phase 1: Fetch raw content
    async with async_sessionmaker() as session:
        async with session.begin():
            repo = SourceRepository(session)
            kb_repo = KnowledgeBaseRepository(session)
            source = await repo.get_by_id(source_id)
            if source is None:
                return
            kb = await kb_repo.get_by_slug(kb_slug)
            if kb is None:
                return
            try:
                content = await fetch_url(source.url)
                source.raw_content = content
                source.status = SourceStatus.processing
            except Exception:
                source.status = SourceStatus.failed

    # Phase 2: Dispatch to appropriate ingest pipeline
    if source and source.raw_content and kb:
        if kb.kb_type == KbType.tool_arsenal:
            await run_tool_arsenal_pipeline(source_id, kb_slug)
        else:
            await run_ingest_pipeline(source_id, kb_slug)


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


@router.post("/batch", response_model=list[SourceResponse], status_code=status.HTTP_201_CREATED)
async def batch_create_sources(
    kb_slug: str, data: BatchSourceCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    kb = await _get_kb(kb_slug, db)
    repo = _source_repo(db)
    sources = []

    for url in data.urls:
        url = url.strip()
        if not url:
            continue
        existing = await repo.get_by_url(kb.id, url)
        if existing:
            sources.append(existing)
            continue
        source = await repo.create(kb_id=kb.id, url=url, status=SourceStatus.processing)
        background_tasks.add_task(_ingest_source, source.id, kb_slug)
        sources.append(source)

    return sources


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
