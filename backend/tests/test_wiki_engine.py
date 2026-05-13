import uuid
from unittest.mock import AsyncMock, MagicMock, patch

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


# --- API-level tests ---


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


# --- Unit tests for lint_wiki function ---


def _make_page(slug: str, title: str, content: str, outgoing_links=None, incoming_links=None):
    page = MagicMock()
    page.slug = slug
    page.title = title
    page.content = content
    page.outgoing_links = outgoing_links or []
    page.incoming_links = incoming_links or []
    return page


async def test_lint_wiki_empty_kb() -> None:
    from app.services.wiki_engine import lint_wiki

    mock_db = MagicMock()
    with patch("app.repositories.wiki_page.WikiPageRepository") as mock_repo_cls:
        mock_repo_cls.return_value.list_by_kb = AsyncMock(return_value=[])
        result = await lint_wiki(str(uuid.uuid4()), "test-kb", mock_db)

    assert result["status"] == "empty"
    assert result["issues"] == []
    assert result["suggestions"] == []


async def test_lint_wiki_detects_orphan_pages() -> None:
    from app.services.wiki_engine import lint_wiki

    pages = [
        _make_page("index", "Index", "Main index page content here", incoming_links=["concept-a"]),
        _make_page("orphan", "Orphan Page", "A page with no incoming links at all"),
    ]

    mock_db = MagicMock()
    with (
        patch("app.repositories.wiki_page.WikiPageRepository") as mock_repo_cls,
        patch("app.services.wiki_engine.generate", new_callable=AsyncMock) as mock_gen,
    ):
        mock_repo_cls.return_value.list_by_kb = AsyncMock(return_value=pages)
        mock_gen.return_value = '{"contradictions": [], "suggestions": []}'
        result = await lint_wiki(str(uuid.uuid4()), "test-kb", mock_db)

    assert result["status"] == "checked"
    orphan_issue = next((i for i in result["structural_issues"] if i["type"] == "orphan_pages"), None)
    assert orphan_issue is not None
    assert "orphan" in orphan_issue["pages"]


async def test_lint_wiki_detects_broken_links() -> None:
    from app.services.wiki_engine import lint_wiki

    pages = [
        _make_page(
            "page-a",
            "Page A",
            "Content with a broken link",
            outgoing_links=["missing-page"],
            incoming_links=["page-b"],
        ),
        _make_page("page-b", "Page B", "Another page", outgoing_links=["page-a"], incoming_links=[]),
    ]

    mock_db = MagicMock()
    with (
        patch("app.repositories.wiki_page.WikiPageRepository") as mock_repo_cls,
        patch("app.services.wiki_engine.generate", new_callable=AsyncMock) as mock_gen,
    ):
        mock_repo_cls.return_value.list_by_kb = AsyncMock(return_value=pages)
        mock_gen.return_value = '{"contradictions": [], "suggestions": []}'
        result = await lint_wiki(str(uuid.uuid4()), "test-kb", mock_db)

    broken_issue = next((i for i in result["structural_issues"] if i["type"] == "broken_links"), None)
    assert broken_issue is not None
    assert any(item["broken_link"] == "missing-page" for item in broken_issue["items"])


async def test_lint_wiki_detects_empty_pages() -> None:
    from app.services.wiki_engine import lint_wiki

    pages = [
        _make_page("index", "Index", "Full index content " * 10, incoming_links=["empty"]),
        _make_page("empty", "Empty Page", "", incoming_links=["index"]),
        _make_page("tiny", "Tiny Page", "Hi", incoming_links=["index"]),
    ]

    mock_db = MagicMock()
    with (
        patch("app.repositories.wiki_page.WikiPageRepository") as mock_repo_cls,
        patch("app.services.wiki_engine.generate", new_callable=AsyncMock) as mock_gen,
    ):
        mock_repo_cls.return_value.list_by_kb = AsyncMock(return_value=pages)
        mock_gen.return_value = '{"contradictions": [], "suggestions": []}'
        result = await lint_wiki(str(uuid.uuid4()), "test-kb", mock_db)

    empty_issue = next((i for i in result["structural_issues"] if i["type"] == "empty_pages"), None)
    assert empty_issue is not None
    assert "empty" in empty_issue["pages"]
    assert "tiny" in empty_issue["pages"]


async def test_lint_wiki_llm_failure_falls_back_gracefully() -> None:
    from app.services.wiki_engine import lint_wiki

    pages = [_make_page("page-a", "Page A", "Some content " * 20, incoming_links=[])]

    mock_db = MagicMock()
    with (
        patch("app.repositories.wiki_page.WikiPageRepository") as mock_repo_cls,
        patch("app.services.wiki_engine.generate", new_callable=AsyncMock, side_effect=RuntimeError("LLM down")),
    ):
        mock_repo_cls.return_value.list_by_kb = AsyncMock(return_value=pages)
        result = await lint_wiki(str(uuid.uuid4()), "test-kb", mock_db)

    assert result["status"] == "checked"
    assert result["llm_analysis"] is None
    assert result["structural_issues"] is not None


async def test_lint_wiki_llm_returns_valid_json() -> None:
    from app.services.wiki_engine import lint_wiki

    pages = [_make_page("page-a", "Page A", "Some content " * 20, incoming_links=["index"])]
    llm_json = '{"contradictions": [{"pages": ["a", "b"], "desc": "矛盾描述"}], "suggestions": ["添加引用"]}'

    mock_db = MagicMock()
    with (
        patch("app.repositories.wiki_page.WikiPageRepository") as mock_repo_cls,
        patch("app.services.wiki_engine.generate", new_callable=AsyncMock, return_value=llm_json),
    ):
        mock_repo_cls.return_value.list_by_kb = AsyncMock(return_value=pages)
        result = await lint_wiki(str(uuid.uuid4()), "test-kb", mock_db)

    assert result["status"] == "checked"
    assert result["llm_analysis"] is not None
    assert "contradictions" in result["llm_analysis"]


async def test_lint_wiki_healthy_kb_no_issues() -> None:
    from app.services.wiki_engine import lint_wiki

    pages = [
        _make_page("index", "Index", "Index page with " * 20, outgoing_links=["page-a"], incoming_links=[]),
        _make_page(
            "page-a",
            "Page A",
            "Well-linked page with " * 20,
            outgoing_links=["index"],
            incoming_links=["index"],
        ),
    ]

    mock_db = MagicMock()
    with (
        patch("app.repositories.wiki_page.WikiPageRepository") as mock_repo_cls,
        patch(
            "app.services.wiki_engine.generate",
            new_callable=AsyncMock,
            return_value='{"contradictions": [], "suggestions": []}',
        ),
    ):
        mock_repo_cls.return_value.list_by_kb = AsyncMock(return_value=pages)
        result = await lint_wiki(str(uuid.uuid4()), "test-kb", mock_db)

    assert result["status"] == "checked"
    assert result["structural_issues"] == []
