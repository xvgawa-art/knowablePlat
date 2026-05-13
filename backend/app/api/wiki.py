from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.knowledge_base import KnowledgeBase
from app.models.wiki_page import WikiPageType
from app.repositories.activity_log import ActivityLogRepository
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.repositories.wiki_page import WikiPageRepository
from app.schemas.wiki import (
    ActivityLogResponse,
    WikiGraphData,
    WikiPageListItem,
    WikiPageResponse,
    WikiQueryRequest,
    WikiQueryResponse,
)

router = APIRouter(prefix="/api/kb/{kb_slug}/wiki", tags=["wiki"])


async def _get_kb(kb_slug: str, db: AsyncSession) -> KnowledgeBase:
    repo = KnowledgeBaseRepository(db)
    kb = await repo.get_by_slug(kb_slug)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
    return kb


@router.get("", response_model=list[WikiPageListItem])
async def list_wiki_pages(
    kb_slug: str,
    page_type: str | None = None,
    search: str | None = None,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    kb = await _get_kb(kb_slug, db)
    wiki_repo = WikiPageRepository(db)
    if search and search.strip():
        return await wiki_repo.search(kb.id, search.strip(), offset=offset, limit=limit)
    ptype = WikiPageType(page_type) if page_type else None
    pages = await wiki_repo.list_by_kb(kb.id, page_type=ptype, offset=offset, limit=limit)
    return pages


@router.get("/graph", response_model=WikiGraphData)
async def get_wiki_graph(kb_slug: str, db: AsyncSession = Depends(get_db)):
    kb = await _get_kb(kb_slug, db)
    wiki_repo = WikiPageRepository(db)
    pages = await wiki_repo.list_by_kb(kb.id, limit=500)

    nodes = [{"id": str(p.id), "slug": p.slug, "title": p.title, "type": p.page_type} for p in pages]
    edges = []
    slug_to_id = {p.slug: str(p.id) for p in pages}

    for page in pages:
        source_id = str(page.id)
        for target_slug in page.outgoing_links or []:
            target_id = slug_to_id.get(target_slug)
            if target_id:
                edges.append({"source": source_id, "target": target_id})

    return WikiGraphData(nodes=nodes, edges=edges)


@router.get("/log", response_model=list[ActivityLogResponse])
async def get_activity_log(kb_slug: str, offset: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    kb = await _get_kb(kb_slug, db)
    log_repo = ActivityLogRepository(db)
    return await log_repo.list_by_kb(kb.id, offset=offset, limit=limit)


@router.get("/{slug}", response_model=WikiPageResponse)
async def get_wiki_page(kb_slug: str, slug: str, db: AsyncSession = Depends(get_db)):
    kb = await _get_kb(kb_slug, db)
    wiki_repo = WikiPageRepository(db)
    page = await wiki_repo.get_by_slug(kb.id, slug)
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wiki 页面不存在")
    return page


@router.post("/query", response_model=WikiQueryResponse)
async def query_wiki(kb_slug: str, data: WikiQueryRequest, db: AsyncSession = Depends(get_db)):
    kb = await _get_kb(kb_slug, db)
    wiki_repo = WikiPageRepository(db)

    index_page = await wiki_repo.get_by_slug(kb.id, "index")
    index_content = index_page.content if index_page else ""

    from app.services.query import answer_question

    answer, referenced = await answer_question(kb.id, kb_slug, data.question, index_content, db)
    return WikiQueryResponse(answer=answer, referenced_pages=referenced)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wiki_page(kb_slug: str, slug: str, db: AsyncSession = Depends(get_db)):
    kb = await _get_kb(kb_slug, db)
    wiki_repo = WikiPageRepository(db)
    page = await wiki_repo.get_by_slug(kb.id, slug)
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wiki 页面不存在")

    # Clean up incoming_links references from other pages
    all_pages = await wiki_repo.list_by_kb(kb.id, limit=500)
    for other in all_pages:
        if other.id == page.id:
            continue
        if other.incoming_links and slug in other.incoming_links:
            updated = [s for s in other.incoming_links if s != slug]
            await wiki_repo.update(other, incoming_links=updated)
        if other.outgoing_links and slug in other.outgoing_links:
            updated = [s for s in other.outgoing_links if s != slug]
            await wiki_repo.update(other, outgoing_links=updated)

    await wiki_repo.delete(page)
