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


async def test_search_wiki_pages(client: AsyncClient, kb_slug: str) -> None:
    from app.database import async_sessionmaker
    from app.repositories.wiki_page import WikiPageRepository

    async with async_sessionmaker() as session:
        async with session.begin():
            from app.repositories.knowledge_base import KnowledgeBaseRepository

            kb_repo = KnowledgeBaseRepository(session)
            kb = await kb_repo.get_by_slug(kb_slug)
            assert kb is not None

            wiki_repo = WikiPageRepository(session)
            await wiki_repo.create(
                kb_id=kb.id,
                slug="xss-attack",
                title="XSS 攻击防护指南",
                page_type="concept",
                content="跨站脚本攻击（XSS）是一种 Web 安全漏洞",
                source_ids=[],
                outgoing_links=[],
                incoming_links=[],
            )
            await wiki_repo.create(
                kb_id=kb.id,
                slug="csrf-defense",
                title="CSRF 防御策略",
                page_type="concept",
                content="跨站请求伪造（CSRF）的防御方法",
                source_ids=[],
                outgoing_links=[],
                incoming_links=[],
            )

    resp = await client.get(f"/api/kb/{kb_slug}/wiki", params={"search": "XSS"})
    assert resp.status_code == 200
    pages = resp.json()
    assert len(pages) == 1
    assert pages[0]["slug"] == "xss-attack"

    resp2 = await client.get(f"/api/kb/{kb_slug}/wiki", params={"search": "CSRF"})
    assert resp2.status_code == 200
    pages2 = resp2.json()
    assert len(pages2) == 1
    assert pages2[0]["slug"] == "csrf-defense"

    resp3 = await client.get(f"/api/kb/{kb_slug}/wiki", params={"search": "不存在的关键词"})
    assert resp3.status_code == 200
    assert resp3.json() == []


async def test_semantic_search(client: AsyncClient, kb_slug: str) -> None:
    from app.database import async_sessionmaker
    from app.repositories.wiki_page import WikiPageRepository

    page_id = uuid.uuid4()
    async with async_sessionmaker() as session:
        async with session.begin():
            from app.repositories.knowledge_base import KnowledgeBaseRepository

            kb_repo = KnowledgeBaseRepository(session)
            kb = await kb_repo.get_by_slug(kb_slug)
            assert kb is not None

            wiki_repo = WikiPageRepository(session)
            page = await wiki_repo.create(
                kb_id=kb.id,
                slug="sql-injection",
                title="SQL 注入攻击",
                page_type="concept",
                content="SQL 注入是一种将恶意 SQL 代码插入应用程序查询的技术",
                source_ids=[],
                outgoing_links=[],
                incoming_links=[],
            )
            page_id = page.id

    with (
        patch("app.services.llm.embed") as mock_embed,
        patch.object(WikiPageRepository, "vector_search") as mock_vs,
    ):
        from app.models.wiki_page import WikiPage, WikiPageType

        mock_embed.return_value = [0.1] * 1536
        mock_page = WikiPage(
            kb_id=kb.id,
            slug="sql-injection",
            title="SQL 注入攻击",
            page_type=WikiPageType.concept,
        )
        mock_page.id = page_id
        mock_vs.return_value = [mock_page]

        resp = await client.post(
            f"/api/kb/{kb_slug}/wiki/semantic-search",
            json={"query": "数据库攻击方式", "limit": 5},
        )
        assert resp.status_code == 200
        pages = resp.json()
        assert len(pages) >= 1
        assert pages[0]["slug"] == "sql-injection"
