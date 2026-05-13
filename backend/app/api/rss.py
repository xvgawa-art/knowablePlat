import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.knowledge_base import KnowledgeBase
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.repositories.rss_entry import RssEntryRepository
from app.repositories.rss_feed import RssFeedRepository
from app.schemas.rss import (
    RssEntryResponse,
    RssFeedCreate,
    RssFeedResponse,
    RssFeedUpdate,
)

router = APIRouter(prefix="/api/kb/{kb_slug}/rss", tags=["rss"])


async def _get_kb(kb_slug: str, db: AsyncSession) -> KnowledgeBase:
    repo = KnowledgeBaseRepository(db)
    kb = await repo.get_by_slug(kb_slug)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
    return kb


@router.post("", response_model=RssFeedResponse, status_code=status.HTTP_201_CREATED)
async def create_feed(kb_slug: str, data: RssFeedCreate, db: AsyncSession = Depends(get_db)):
    kb = await _get_kb(kb_slug, db)
    repo = RssFeedRepository(db)
    return await repo.create(
        kb_id=kb.id,
        name=data.name,
        url=data.url,
        feed_type=data.feed_type,
        poll_interval=data.poll_interval,
        filter_keywords=data.filter_keywords,
        filter_authors=data.filter_authors,
        filter_categories=data.filter_categories,
    )


@router.get("", response_model=list[RssFeedResponse])
async def list_feeds(kb_slug: str, offset: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    kb = await _get_kb(kb_slug, db)
    repo = RssFeedRepository(db)
    return await repo.list_by_kb(kb.id, offset=offset, limit=limit)


@router.get("/{feed_id}", response_model=RssFeedResponse)
async def get_feed(kb_slug: str, feed_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await _get_kb(kb_slug, db)
    repo = RssFeedRepository(db)
    feed = await repo.get_by_id(feed_id)
    if feed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订阅源不存在")
    return feed


@router.put("/{feed_id}", response_model=RssFeedResponse)
async def update_feed(kb_slug: str, feed_id: uuid.UUID, data: RssFeedUpdate, db: AsyncSession = Depends(get_db)):
    await _get_kb(kb_slug, db)
    repo = RssFeedRepository(db)
    feed = await repo.get_by_id(feed_id)
    if feed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订阅源不存在")
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    return await repo.update(feed, **updates)


@router.delete("/{feed_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feed(kb_slug: str, feed_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await _get_kb(kb_slug, db)
    repo = RssFeedRepository(db)
    feed = await repo.get_by_id(feed_id)
    if feed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订阅源不存在")
    await repo.delete(feed)


@router.post("/{feed_id}/fetch", response_model=dict)
async def trigger_fetch(
    kb_slug: str, feed_id: uuid.UUID, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    await _get_kb(kb_slug, db)
    repo = RssFeedRepository(db)
    feed = await repo.get_by_id(feed_id)
    if feed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订阅源不存在")

    from app.services.rss_fetcher import poll_feed

    new_count = await poll_feed(str(feed_id), kb_slug)
    return {"feed_id": str(feed_id), "new_entries": new_count}


@router.get("/{feed_id}/entries", response_model=list[RssEntryResponse])
async def list_entries(
    kb_slug: str, feed_id: uuid.UUID, offset: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)
):
    await _get_kb(kb_slug, db)
    entry_repo = RssEntryRepository(db)
    return await entry_repo.list_by_feed(feed_id, offset=offset, limit=limit)
