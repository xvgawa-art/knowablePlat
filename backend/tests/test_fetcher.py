from unittest.mock import AsyncMock, patch

import pytest


async def test_fetch_url_returns_markdown() -> None:
    from app.services.fetcher import fetch_url

    mock_response = AsyncMock()
    mock_response.text = "# Test Article\n\nSome content here."
    mock_response.raise_for_status = lambda: None

    with patch("app.services.fetcher.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await fetch_url("https://example.com/article")
        assert "# Test Article" in result


async def test_fetch_url_raises_on_empty_content() -> None:
    from app.services.fetcher import fetch_url

    mock_response = AsyncMock()
    mock_response.text = "   "
    mock_response.raise_for_status = lambda: None

    with patch("app.services.fetcher.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(ValueError, match="Empty content"):
            await fetch_url("https://example.com/empty")


async def test_fetch_url_raises_on_http_error() -> None:
    import httpx

    from app.services.fetcher import fetch_url

    with patch("app.services.fetcher.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPError("Connection failed")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(ValueError, match="Failed to fetch"):
            await fetch_url("https://example.com/fail")
