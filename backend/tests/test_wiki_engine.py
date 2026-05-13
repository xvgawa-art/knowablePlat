import uuid
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def kb_slug(client: AsyncClient) -> str:
    uid = uuid.uuid4().hex[:8]
    resp = await client.post("/api/knowledge-bases", json={"name": f"lint-{uid}", "slug": f"lint-{uid}"})
    return resp.json()["slug"]


async def test_lint_empty_kb(client: AsyncClient, kb_slug: str) -> None:
    resp = await client.post(f"/api/kb/{kb_slug}/wiki/lint")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "empty"


async def test_lint_with_pages(client: AsyncClient, kb_slug: str) -> None:
    from app.database import async_sessionmaker
    from app.models.wiki_page import WikiPageType
    from app.repositories.knowledge_base import KnowledgeBaseRepository
    from app.repositories.wiki_page import WikiPageRepository

    async with async_sessionmaker() as session:
        async with session.begin():
            kb_repo = KnowledgeBaseRepository(session)
            kb = await kb_repo.get_by_slug(kb_slug)

            wiki_repo = WikiPageRepository(session)
            await wiki_repo.create(
                kb_id=kb.id,
                slug="orphan-page",
                title="孤儿页面",
                page_type=WikiPageType.concept,
                content="这是一个孤儿页面，没有其他页面链接到它",
                source_ids=[],
                outgoing_links=[],
                incoming_links=[],
            )
            await wiki_repo.create(
                kb_id=kb.id,
                slug="page-with-broken-link",
                title="有损坏链接的页面",
                page_type=WikiPageType.concept,
                content="这个页面链接到一个不存在的页面",
                source_ids=[],
                outgoing_links=["nonexistent-page"],
                incoming_links=[],
            )

    with patch("app.services.wiki_engine.generate") as mock_generate:
        mock_generate.return_value = '{"contradictions": [], "suggestions": ["添加更多交叉引用"]}'
        resp = await client.post(f"/api/kb/{kb_slug}/wiki/lint")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "checked"
    assert data["page_count"] == 2
    structural = data["structural_issues"]
    types = [issue["type"] for issue in structural]
    assert "orphan_pages" in types
    assert "broken_links" in types


async def test_lint_kb_not_found(client: AsyncClient) -> None:
    resp = await client.post("/api/kb/nonexistent/wiki/lint")
    assert resp.status_code == 404
