from unittest.mock import AsyncMock, patch

import httpx
import pytest


async def test_fetch_url_uses_jina_when_firecrawl_not_configured() -> None:
    from app.services.fetcher import fetch_url

    mock_response = AsyncMock()
    mock_response.text = "# Test Article\n\nSome content here."
    mock_response.raise_for_status = lambda: None

    with (
        patch("app.services.fetcher.settings") as mock_settings,
        patch("app.services.fetcher.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_settings.firecrawl_api_url = ""
        mock_settings.firecrawl_api_key = ""
        mock_settings.jina_reader_url = "https://r.jina.ai/"

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await fetch_url("https://example.com/article")
        assert "# Test Article" in result


async def test_fetch_url_falls_back_to_jina_when_firecrawl_fails() -> None:
    from app.services.fetcher import fetch_url

    jina_response = AsyncMock()
    jina_response.text = "# Jina Content"
    jina_response.raise_for_status = lambda: None

    with (
        patch("app.services.fetcher.settings") as mock_settings,
        patch("app.services.fetcher.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_settings.firecrawl_api_url = "https://firecrawl.example.com"
        mock_settings.firecrawl_api_key = "test-key"
        mock_settings.jina_reader_url = "https://r.jina.ai/"

        mock_client = AsyncMock()
        # First call (firecrawl POST) fails, second call (jina GET) succeeds
        mock_client.post.side_effect = httpx.HTTPError("Firecrawl down")
        mock_client.get.return_value = jina_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await fetch_url("https://example.com/article")
        assert "# Jina Content" in result


async def test_fetch_url_falls_back_to_raw_http_when_jina_fails() -> None:
    from app.services.fetcher import fetch_url

    raw_response = AsyncMock()
    raw_response.text = "<html><body><h1>Raw Content</h1><p>Text here.</p></body></html>"
    raw_response.raise_for_status = lambda: None

    with (
        patch("app.services.fetcher.settings") as mock_settings,
        patch("app.services.fetcher.httpx.AsyncClient") as mock_client_cls,
        patch("app.services.fetcher._fetch_via_firecrawl", side_effect=Exception("no firecrawl")),
        patch("app.services.fetcher._fetch_via_jina", side_effect=Exception("jina failed")),
    ):
        mock_settings.firecrawl_api_url = ""
        mock_settings.jina_reader_url = "https://r.jina.ai/"

        mock_client = AsyncMock()
        mock_client.get.return_value = raw_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await fetch_url("https://example.com/article")
        assert "Raw Content" in result


async def test_fetch_url_raises_when_all_fail() -> None:
    from app.services.fetcher import fetch_url

    with (
        patch("app.services.fetcher._fetch_via_firecrawl", side_effect=Exception("fc fail")),
        patch("app.services.fetcher._fetch_via_jina", side_effect=Exception("jina fail")),
        patch("app.services.fetcher._fetch_via_raw_http", side_effect=Exception("raw fail")),
    ):
        with pytest.raises(ValueError, match="All fetchers failed"):
            await fetch_url("https://example.com/fail")


async def test_fetch_via_firecrawl_success() -> None:
    from app.services.fetcher import _fetch_via_firecrawl

    mock_response = AsyncMock()
    mock_response.raise_for_status = lambda: None
    # json() is not async on httpx.Response — use regular Mock
    mock_response.json = lambda: {"data": {"markdown": "# Firecrawl Article\n\nContent."}}

    with (
        patch("app.services.fetcher.settings") as mock_settings,
        patch("app.services.fetcher.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_settings.firecrawl_api_url = "https://api.firecrawl.dev"
        mock_settings.firecrawl_api_key = "fc-test-key"

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await _fetch_via_firecrawl("https://example.com/article")
        assert "# Firecrawl Article" in result


async def test_fetch_via_firecrawl_skipped_when_not_configured() -> None:
    from app.services.fetcher import _fetch_via_firecrawl

    with patch("app.services.fetcher.settings") as mock_settings:
        mock_settings.firecrawl_api_url = ""
        mock_settings.firecrawl_api_key = ""

        with pytest.raises(ValueError, match="not configured"):
            await _fetch_via_firecrawl("https://example.com/article")
