import json
from unittest.mock import AsyncMock, patch


async def test_generate_notification_parses_json() -> None:
    from app.services.notification import generate_ingest_notification

    mock_response = json.dumps({
        "summary": "本文介绍了新型 XSS 攻击的防护策略。",
        "related_points": [
            {"wiki_page_slug": "xss-attack", "title": "XSS 攻击", "relation_desc": "与已有知识互补"},
        ],
    })

    wiki_pages = [{"title": "XSS 攻击", "slug": "xss-attack"}]
    with patch("app.services.notification.generate", new_callable=AsyncMock, return_value=mock_response):
        result = await generate_ingest_notification("测试文章", "测试摘要", wiki_pages)
        assert "XSS" in result["summary"]
        assert len(result["related_points"]) == 1
        assert result["related_points"][0]["wiki_page_slug"] == "xss-attack"


async def test_generate_notification_no_wiki_pages() -> None:
    from app.services.notification import generate_ingest_notification

    mock_response = json.dumps({"summary": "测试总结。", "related_points": []})

    with patch("app.services.notification.generate", new_callable=AsyncMock, return_value=mock_response):
        result = await generate_ingest_notification("测试", "摘要", [])
        assert result["summary"] == "测试总结。"
        assert result["related_points"] == []


async def test_generate_notification_handles_invalid_json() -> None:
    from app.services.notification import generate_ingest_notification

    with patch("app.services.notification.generate", new_callable=AsyncMock, return_value="不是JSON"):
        result = await generate_ingest_notification("测试", "这是一个摘要", [])
        assert result["summary"] == "这是一个摘要"
        assert result["related_points"] == []
