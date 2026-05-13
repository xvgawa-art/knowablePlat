import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()


async def _fetch_via_firecrawl(url: str) -> str:
    """Fetch URL via Firecrawl API. Returns Markdown or raises."""
    if not settings.firecrawl_api_url or not settings.firecrawl_api_key:
        raise ValueError("Firecrawl not configured")

    api_url = f"{settings.firecrawl_api_url}/v1/scrape"
    headers = {"Authorization": f"Bearer {settings.firecrawl_api_key}", "Content-Type": "application/json"}
    payload = {"url": url, "formats": ["markdown"]}

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(api_url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("data", {}).get("markdown", "")
        if not content.strip():
            raise ValueError(f"Empty content from Firecrawl for {url}")
        return content


async def _fetch_via_jina(url: str) -> str:
    """Fetch URL via Jina Reader API. Returns Markdown or raises."""
    jina_url = f"{settings.jina_reader_url}{url}"
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        resp = await client.get(jina_url)
        resp.raise_for_status()
        content = resp.text
        if not content.strip():
            raise ValueError(f"Empty content from Jina Reader for {url}")
        return content


async def _fetch_via_raw_http(url: str) -> str:
    """Fetch raw HTML and extract text as last resort."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; KnowablePlat/1.0)"})
        resp.raise_for_status()
        html = resp.text

    try:
        from readability import Document

        doc = Document(html)
        text = doc.summary()
    except ImportError:
        text = html

    try:
        from markdownify import markdownify as md

        content = md(text, heading_style="ATX")
    except ImportError:
        content = text

    if not content.strip():
        raise ValueError(f"Empty content from raw HTTP for {url}")
    return content


async def fetch_url(url: str) -> str:
    """Fetch a URL and convert to clean Markdown.

    Fallback chain: Firecrawl → Jina Reader → raw HTTP + readability.
    """
    # Try Firecrawl first
    try:
        content = await _fetch_via_firecrawl(url)
        logger.info("url_fetched", fetcher="firecrawl", url=url, content_len=len(content))
        return content
    except Exception as e:
        logger.debug("fetch_firecrawl_skipped", url=url, error=str(e))

    # Try Jina Reader
    try:
        content = await _fetch_via_jina(url)
        logger.info("url_fetched", fetcher="jina", url=url, content_len=len(content))
        return content
    except Exception as e:
        logger.warning("fetch_jina_failed", url=url, error=str(e))

    # Last resort: raw HTTP + readability
    try:
        content = await _fetch_via_raw_http(url)
        logger.info("url_fetched", fetcher="raw_http", url=url, content_len=len(content))
        return content
    except Exception as e:
        logger.error("fetch_all_failed", url=url, error=str(e))
        raise ValueError(f"All fetchers failed for {url}") from e
