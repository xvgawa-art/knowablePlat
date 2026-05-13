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


async def test_extract_tool_info_with_usage() -> None:
    from app.services.llm import LLMResponse
    from app.services.tool_arsenal import _extract_tool_info_with_usage

    mock_response = json.dumps({"name": "Nmap", "description": "扫描器", "category": "信息收集"})
    mock_llm = AsyncMock(return_value=LLMResponse(mock_response, 50, 100))
    with patch("app.services.tool_arsenal.generate_with_usage", mock_llm):
        result, tokens = await _extract_tool_info_with_usage("content")
        assert result["name"] == "Nmap"
        assert tokens == 150


async def test_categorize_tool_with_usage() -> None:
    from app.services.llm import LLMResponse
    from app.services.tool_arsenal import _categorize_tool_with_usage

    mock_response = json.dumps({"category": "Web安全", "category_slug": "web-security"})
    mock_llm = AsyncMock(return_value=LLMResponse(mock_response, 30, 60))
    with patch("app.services.tool_arsenal.generate_with_usage", mock_llm):
        result, tokens = await _categorize_tool_with_usage({"name": "test"})
        assert result["category"] == "Web安全"
        assert tokens == 90


async def test_generate_tool_page_with_usage() -> None:
    from app.services.llm import LLMResponse
    from app.services.tool_arsenal import _generate_tool_page_with_usage

    mock_llm = AsyncMock(return_value=LLMResponse("# Nmap\n\n简介...", 40, 80))
    with patch("app.services.tool_arsenal.generate_with_usage", mock_llm):
        content, tokens = await _generate_tool_page_with_usage({"name": "Nmap"}, [])
        assert "# Nmap" in content
        assert tokens == 120


async def test_extract_tool_info_with_usage_invalid_json() -> None:
    from app.services.llm import LLMResponse
    from app.services.tool_arsenal import _extract_tool_info_with_usage

    mock_llm = AsyncMock(return_value=LLMResponse("not json at all", 10, 20))
    with patch("app.services.tool_arsenal.generate_with_usage", mock_llm):
        result, tokens = await _extract_tool_info_with_usage("content")
        assert result["name"] == "未知工具"
        assert tokens == 30


async def test_categorize_tool_with_usage_invalid_json() -> None:
    from app.services.llm import LLMResponse
    from app.services.tool_arsenal import _categorize_tool_with_usage

    mock_llm = AsyncMock(return_value=LLMResponse("garbage", 10, 15))
    with patch("app.services.tool_arsenal.generate_with_usage", mock_llm):
        result, tokens = await _categorize_tool_with_usage({"name": "test"})
        assert result["category"] == "其他"
        assert result["category_slug"] == "other"
        assert tokens == 25


async def test_categorize_tool_invalid_json() -> None:
    from app.services.tool_arsenal import _categorize_tool

    with patch("app.services.tool_arsenal.generate", new_callable=AsyncMock, return_value="not json"):
        result = await _categorize_tool({"name": "test"})
        assert result["category"] == "其他"
        assert result["category_slug"] == "other"


async def test_generate_tool_page_with_existing_tools() -> None:
    from app.services.tool_arsenal import _generate_tool_page

    existing = [{"title": "Nmap", "slug": "nmap"}, {"title": "Burp Suite", "slug": "burp-suite"}]
    with patch(
        "app.services.tool_arsenal.generate", new_callable=AsyncMock, return_value="# 新工具\n\n相关工具"
    ) as mock_gen:
        result = await _generate_tool_page({"name": "新工具"}, existing)
        assert "# 新工具" in result
        call_args = mock_gen.call_args[0][0]
        assert "Nmap" in call_args


async def test_generate_category_page_with_recommendations() -> None:
    from app.services.tool_arsenal import _generate_category_page

    tools = [{"title": "Nmap", "slug": "nmap"}]
    recs = [
        {"scenario": "端口扫描", "recommended": "Nmap"},
        {"scenario": "漏洞扫描", "recommended": "Nessus"},
        {"scenario": "", "recommended": ""},
    ]
    result = await _generate_category_page("网络扫描", "network-scan", tools, recs)
    assert "端口扫描" in result
    assert "nmap" in result
    assert "nessus" in result
