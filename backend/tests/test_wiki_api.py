import uuid

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
    resp = await client.post("/api/knowledge-bases", json={"name": f"测试-{uid}", "slug": f"test-{uid}"})
    return resp.json()["slug"]


@pytest.fixture
async def kb_with_wiki(client: AsyncClient, kb_slug: str) -> str:
    """Create a KB with a wiki page via the ingest pipeline (directly creating in DB)."""
    from app.database import async_sessionmaker
    from app.models.wiki_page import WikiPage, WikiPageType

    async with async_sessionmaker() as session:
        async with session.begin():
            from app.repositories.knowledge_base import KnowledgeBaseRepository

            kb_repo = KnowledgeBaseRepository(session)
            kb = await kb_repo.get_by_slug(kb_slug)
            assert kb is not None

            page = WikiPage(
                kb_id=kb.id,
                slug="test-page",
                title="测试页面",
                page_type=WikiPageType.source,
                content="# 测试页面\n\n这是测试内容",
                source_ids=[],
                outgoing_links=[],
                incoming_links=[],
            )
            session.add(page)
    return kb_slug


async def test_list_wiki_pages_empty(client: AsyncClient, kb_slug: str) -> None:
    resp = await client.get(f"/api/kb/{kb_slug}/wiki")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_wiki_pages_with_data(client: AsyncClient, kb_with_wiki: str) -> None:
    resp = await client.get(f"/api/kb/{kb_with_wiki}/wiki")
    assert resp.status_code == 200
    pages = resp.json()
    assert len(pages) >= 1
    assert pages[0]["slug"] == "test-page"


async def test_get_wiki_page(client: AsyncClient, kb_with_wiki: str) -> None:
    resp = await client.get(f"/api/kb/{kb_with_wiki}/wiki/test-page")
    assert resp.status_code == 200
    page = resp.json()
    assert page["title"] == "测试页面"
    assert "# 测试页面" in page["content"]


async def test_get_wiki_page_not_found(client: AsyncClient, kb_slug: str) -> None:
    resp = await client.get(f"/api/kb/{kb_slug}/wiki/nonexistent")
    assert resp.status_code == 404


async def test_wiki_graph(client: AsyncClient, kb_with_wiki: str) -> None:
    resp = await client.get(f"/api/kb/{kb_with_wiki}/wiki/graph")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 1


async def test_activity_log_empty(client: AsyncClient, kb_slug: str) -> None:
    resp = await client.get(f"/api/kb/{kb_slug}/wiki/log")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_delete_wiki_page(client: AsyncClient, kb_with_wiki: str) -> None:
    resp = await client.delete(f"/api/kb/{kb_with_wiki}/wiki/test-page")
    assert resp.status_code == 204

    resp = await client.get(f"/api/kb/{kb_with_wiki}/wiki/test-page")
    assert resp.status_code == 404


async def test_wiki_kb_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/kb/nonexistent/wiki")
    assert resp.status_code == 404
