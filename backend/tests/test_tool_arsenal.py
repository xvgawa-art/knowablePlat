import json
from unittest.mock import AsyncMock, patch


async def test_extract_tool_info_parses_json() -> None:
    from app.services.tool_arsenal import _extract_tool_info

    mock_response = json.dumps(
        {
            "name": "Nmap",
            "description": "网络扫描和安全审计工具",
            "purpose": "端口扫描和服务识别",
            "advantages": ["开源免费", "支持多种扫描技术"],
            "scenarios": ["资产发现", "端口扫描"],
            "category": "信息收集",
            "homepage": "https://nmap.org",
            "license": "GPL",
            "platforms": ["Windows", "Linux", "macOS"],
            "tags": ["扫描", "网络"],
        }
    )

    with patch("app.services.tool_arsenal.generate", new_callable=AsyncMock, return_value=mock_response):
        result = await _extract_tool_info("some tool content")
        assert result["name"] == "Nmap"
        assert result["category"] == "信息收集"
        assert len(result["advantages"]) == 2


async def test_extract_tool_info_handles_invalid_json() -> None:
    from app.services.tool_arsenal import _extract_tool_info

    with patch("app.services.tool_arsenal.generate", new_callable=AsyncMock, return_value="不是JSON"):
        result = await _extract_tool_info("content")
        assert result["name"] == "未知工具"


async def test_categorize_tool() -> None:
    from app.services.tool_arsenal import _categorize_tool

    mock_response = json.dumps(
        {
            "category": "Web安全",
            "category_slug": "web-security",
            "scenario_recommendations": [
                {"scenario": "XSS 检测", "recommended": "Burp Suite"},
            ],
        }
    )

    with patch("app.services.tool_arsenal.generate", new_callable=AsyncMock, return_value=mock_response):
        result = await _categorize_tool({"name": "test"})
        assert result["category"] == "Web安全"
        assert result["category_slug"] == "web-security"


async def test_generate_tool_page() -> None:
    from app.services.tool_arsenal import _generate_tool_page

    with patch("app.services.tool_arsenal.generate", new_callable=AsyncMock, return_value="# Nmap\n\n简介..."):
        result = await _generate_tool_page({"name": "Nmap"}, [])
        assert "# Nmap" in result


async def test_generate_category_page() -> None:
    from app.services.tool_arsenal import _generate_category_page

    tools = [{"title": "Nmap", "slug": "nmap"}, {"title": "Masscan", "slug": "masscan"}]
    recs = [{"scenario": "快速扫描", "recommended": "Masscan"}]
    result = await _generate_category_page("信息收集", "info-gathering", tools, recs)
    assert "信息收集" in result
    assert "nmap" in result
    assert "masscan" in result
    assert "快速扫描" in result


async def test_generate_category_page_empty() -> None:
    from app.services.tool_arsenal import _generate_category_page

    result = await _generate_category_page("测试", "test", [], [])
    assert "测试" in result
    assert "暂无推荐" in result


async def test_tool_slugify() -> None:
    from app.services.tool_arsenal import _slugify

    assert _slugify("Burp Suite") == "burp-suite"
    assert _slugify("SQLMap") == "sqlmap"
