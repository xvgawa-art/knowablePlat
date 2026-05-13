import json
import uuid
from unittest.mock import AsyncMock, patch

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


async def test_slugify_basic() -> None:
    from app.services.ingest import _slugify

    assert _slugify("Hello World") == "hello-world"
    assert _slugify("  测试 Title  ") == "测试-title"
    assert _slugify("API安全测试") == "api安全测试"
    assert _slugify("") == "untitled"
    assert _slugify("a" * 300) == "a" * 200


async def test_extract_parses_json() -> None:
    from app.services.ingest import _extract

    mock_response = json.dumps(
        {
            "title": "测试文章",
            "summary": "这是一个测试摘要",
            "key_points": ["要点1", "要点2"],
            "entities": [{"name": "Python", "type": "tool"}],
            "topics": ["编程"],
        }
    )

    from app.services.llm import LLMResponse

    mock_llm = AsyncMock(return_value=LLMResponse(mock_response, 100, 200))
    with patch("app.services.ingest.generate_with_usage", mock_llm):
        result, tokens = await _extract("some content")
        assert result["title"] == "测试文章"
        assert result["summary"] == "这是一个测试摘要"
        assert len(result["key_points"]) == 2
        assert len(result["entities"]) == 1
        assert tokens == 300


async def test_extract_handles_invalid_json() -> None:
    from app.services.ingest import _extract
    from app.services.llm import LLMResponse

    mock_llm = AsyncMock(return_value=LLMResponse("这不是JSON", 10, 20))
    with patch("app.services.ingest.generate_with_usage", mock_llm):
        result, tokens = await _extract("some content")
        assert result["title"] == "未知标题"
        assert result["key_points"] == []
        assert tokens == 30


async def test_synthesize_wiki_page() -> None:
    from app.services.ingest import _synthesize_wiki_page

    with patch("app.services.ingest.generate", new_callable=AsyncMock, return_value="# 测试页面\n\n内容"):
        result = await _synthesize_wiki_page("test-kb", "标题", "摘要", {"title": "标题", "key_points": []})
        assert "# 测试页面" in result


async def test_find_cross_references() -> None:
    from app.services.ingest import _find_cross_references

    with patch("app.services.ingest.generate", new_callable=AsyncMock, return_value='["slug1", "slug2"]'):
        result = await _find_cross_references("test-kb", "新页面", "内容", [{"title": "A", "slug": "slug1"}])
        assert result == ["slug1", "slug2"]


async def test_find_cross_references_empty() -> None:
    from app.services.ingest import _find_cross_references

    result = await _find_cross_references("test-kb", "新页面", "内容", [])
    assert result == []


async def test_build_index_content() -> None:
    from app.models.wiki_page import WikiPage, WikiPageType
    from app.services.ingest import _build_index_content

    pages = [
        WikiPage(slug="page-1", title="页面1", page_type=WikiPageType.source, kb_id=uuid.uuid4()),
        WikiPage(slug="page-2", title="页面2", page_type=WikiPageType.entity, kb_id=uuid.uuid4()),
    ]
    result = await _build_index_content(pages)
    assert "来源摘要" in result
    assert "实体" in result
    assert "page-1" in result
    assert "page-2" in result


async def test_embed_wiki_page_success() -> None:
    from app.models.wiki_page import WikiPage, WikiPageType
    from app.services.ingest import _embed_wiki_page

    mock_page = WikiPage(slug="test", title="测试", page_type=WikiPageType.source, kb_id=uuid.uuid4(), content="内容")
    mock_repo = AsyncMock()

    with patch("app.services.ingest.embed", new_callable=AsyncMock, return_value=[0.1, 0.2, 0.3]):
        await _embed_wiki_page(mock_repo, mock_page)
        mock_repo.update_embedding.assert_called_once_with(mock_page, [0.1, 0.2, 0.3])


async def test_embed_wiki_page_handles_failure() -> None:
    from app.models.wiki_page import WikiPage, WikiPageType
    from app.services.ingest import _embed_wiki_page

    mock_page = WikiPage(slug="test", title="测试", page_type=WikiPageType.source, kb_id=uuid.uuid4(), content="内容")
    mock_repo = AsyncMock()

    with patch("app.services.ingest.embed", new_callable=AsyncMock, side_effect=RuntimeError("API error")):
        await _embed_wiki_page(mock_repo, mock_page)
        mock_repo.update_embedding.assert_not_called()
