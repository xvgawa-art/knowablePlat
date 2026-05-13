import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()


async def fetch_url(url: str) -> str:
    """Fetch a URL and convert to clean Markdown using Jina Reader API."""
    jina_url = f"{settings.jina_reader_url}{url}"
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        try:
            resp = await client.get(jina_url)
            resp.raise_for_status()
            content = resp.text
            if not content.strip():
                raise ValueError(f"Empty content from Jina Reader for {url}")
            logger.info("url_fetched", url=url, content_len=len(content))
            return content
        except httpx.HTTPError as e:
            logger.error("fetch_failed", url=url, error=str(e))
            raise ValueError(f"Failed to fetch {url}: {e}") from e
