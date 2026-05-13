import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.wiki_page import WikiPage, WikiPageType


async def test_answer_question_returns_answer_and_references() -> None:
    from app.services.query import answer_question

    kb_id = uuid.uuid4()
    index_content = "# 知识库目录\n\n- [[xss-attack|XSS 攻击]]\n- [[sql-injection|SQL 注入]]"

    page = WikiPage(
        slug="xss-attack",
        title="XSS 攻击",
        page_type=WikiPageType.source,
        kb_id=kb_id,
        content="# XSS 攻击\n\n跨站脚本攻击是一种 Web 安全漏洞。",
    )

    mock_session = MagicMock()
    call_count = 0

    async def mock_generate(prompt, system=""):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return "xss-attack\nsql-injection"
        return "XSS 攻击是一种注入攻击，攻击者在网页中注入恶意脚本。详见 [[xss-attack]]"

    with (
        patch("app.services.query.generate", side_effect=mock_generate),
        patch("app.services.query.WikiPageRepository") as mock_repo_cls,
    ):
        mock_repo = AsyncMock()
        mock_repo.get_by_slug.return_value = page
        mock_repo_cls.return_value = mock_repo

        answer, referenced = await answer_question(kb_id, "test-kb", "什么是XSS攻击？", index_content, mock_session)
        assert "XSS" in answer
        assert "xss-attack" in referenced
        assert call_count == 2


async def test_answer_question_no_relevant_pages() -> None:
    from app.services.query import answer_question

    kb_id = uuid.uuid4()
    index_content = "# 知识库目录\n\n- [[page-a|页面A]]"

    mock_session = MagicMock()
    call_count = 0

    async def mock_generate(prompt, system=""):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return "nonexistent-slug"
        return "根据已有知识，未找到直接相关内容。"

    with (
        patch("app.services.query.generate", side_effect=mock_generate),
        patch("app.services.query.WikiPageRepository") as mock_repo_cls,
    ):
        mock_repo = AsyncMock()
        mock_repo.get_by_slug.return_value = None
        mock_repo_cls.return_value = mock_repo

        answer, referenced = await answer_question(kb_id, "test-kb", "无关问题", index_content, mock_session)
        assert len(answer) > 0
        assert referenced == []


async def test_answer_question_uses_index_as_fallback_context() -> None:
    from app.services.query import answer_question

    kb_id = uuid.uuid4()
    index_content = "# 目录\n\n- [[page-a|A]]"

    mock_session = MagicMock()
    call_count = 0

    async def mock_generate(prompt, system=""):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return ""
        return "通用回答"

    with (
        patch("app.services.query.generate", side_effect=mock_generate),
        patch("app.services.query.WikiPageRepository") as mock_repo_cls,
    ):
        mock_repo = AsyncMock()
        mock_repo_cls.return_value = mock_repo

        answer, referenced = await answer_question(kb_id, "test-kb", "测试", index_content, mock_session)
        assert answer == "通用回答"
        assert referenced == []
