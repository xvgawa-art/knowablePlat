import feedparser
import structlog

from app.models.rss_entry import EntryStatus
from app.models.rss_feed import FetchStatus
from app.repositories.rss_entry import RssEntryRepository
from app.repositories.rss_feed import RssFeedRepository

logger = structlog.get_logger()


def _parse_feed(raw_feed: str, url: str) -> feedparser.FeedParserDict:
    """Parse RSS/Atom feed from raw content."""
    feed = feedparser.parse(raw_feed)
    if feed.bozo and not feed.entries:
        logger.warning("rss_parse_error", url=url, error=str(feed.bozo_exception))
    return feed


def _entry_matches_filters(
    entry: dict,
    keywords: list[str] | None,
    authors: list[str] | None,
    categories: list[str] | None,
) -> bool:
    """Check if an entry matches the configured filters. Returns True if it should be ingested."""
    text = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()

    if keywords and not any(kw.lower() in text for kw in keywords):
        return False

    if authors:
        entry_authors = [a.get("name", "") for a in entry.get("authors", []) if isinstance(a, dict)]
        entry_author_str = " ".join(entry_authors).lower()
        if not any(a.lower() in entry_author_str for a in authors):
            return False

    if categories:
        entry_tags = [t.get("term", "") for t in entry.get("tags", []) if isinstance(t, dict)]
        entry_tag_str = " ".join(entry_tags).lower()
        if not any(c.lower() in entry_tag_str for c in categories):
            return False

    return True


async def poll_feed(feed_id: str, kb_slug: str) -> int:
    """Poll an RSS feed, filter new entries, and queue them for ingestion.

    Returns the number of new entries queued.
    """
    from app.database import async_sessionmaker
    from app.services.fetcher import fetch_url

    async with async_sessionmaker() as session:
        async with session.begin():
            feed_repo = RssFeedRepository(session)
            entry_repo = RssEntryRepository(session)

            feed = await feed_repo.get_by_id(feed_id)
            if feed is None:
                return 0

            try:
                raw_content = await fetch_url(feed.url)
            except Exception as e:
                feed.last_fetch_status = FetchStatus.failed
                feed.last_error = str(e)[:500]
                logger.error("rss_fetch_failed", feed_id=str(feed_id), url=feed.url, error=str(e))
                return 0

            parsed = _parse_feed(raw_content, feed.url)
            new_count = 0

            for entry in parsed.entries:
                guid = entry.get("id") or entry.get("link", "")
                url = entry.get("link", "")
                if not guid or not url:
                    continue

                existing = await entry_repo.get_by_guid(feed.id, guid)
                if existing:
                    continue

                if not _entry_matches_filters(entry, feed.filter_keywords, feed.filter_authors, feed.filter_categories):
                    await entry_repo.create(
                        feed_id=feed.id,
                        kb_id=feed.kb_id,
                        guid=guid,
                        url=url,
                        title=entry.get("title", ""),
                        status=EntryStatus.filtered,
                    )
                    continue

                await entry_repo.create(
                    feed_id=feed.id,
                    kb_id=feed.kb_id,
                    guid=guid,
                    url=url,
                    title=entry.get("title", ""),
                    status=EntryStatus.new,
                )
                new_count += 1

            from datetime import UTC, datetime

            feed.last_fetched_at = datetime.now(UTC).replace(tzinfo=None)
            has_new = new_count > 0 or len(parsed.entries) == 0
            feed.last_fetch_status = FetchStatus.success if has_new else FetchStatus.partial
            feed.last_error = None
            feed.total_fetched += new_count

            logger.info("rss_poll_complete", feed_id=str(feed_id), new_entries=new_count)

    # Ingest new entries outside the poll transaction
    if new_count > 0:
        await ingest_new_entries(feed_id, kb_slug)

    return new_count


async def ingest_new_entries(feed_id: str, kb_slug: str) -> int:
    """Find new RSS entries and run the ingest pipeline for each.

    Returns the number of entries processed.
    """
    from app.database import async_sessionmaker
    from app.models.knowledge_base import KbType
    from app.repositories.knowledge_base import KnowledgeBaseRepository
    from app.repositories.source import SourceRepository
    from app.services.fetcher import fetch_url
    from app.services.ingest import run_ingest_pipeline
    from app.services.tool_arsenal import run_tool_arsenal_pipeline

    processed = 0

    async with async_sessionmaker() as session:
        async with session.begin():
            kb_repo = KnowledgeBaseRepository(session)
            source_repo = SourceRepository(session)

            kb = await kb_repo.get_by_slug(kb_slug)
            if not kb:
                return 0

            from sqlalchemy import select

            from app.models.rss_entry import RssEntry

            result = await session.execute(
                select(RssEntry).where(
                    RssEntry.feed_id == feed_id,
                    RssEntry.status == EntryStatus.new,
                )
            )
            entries = list(result.scalars().all())

            for entry in entries:
                try:
                    entry.status = EntryStatus.ingesting
                    await session.flush()

                    content = await fetch_url(entry.url)
                    from app.models.source import SourceStatus

                    source = await source_repo.create(
                        kb_id=kb.id,
                        url=entry.url,
                        title=entry.title,
                        raw_content=content,
                        status=SourceStatus.processing,
                    )
                    entry.source_id = source.id
                    await session.flush()

                    from app.services.filesystem import save_raw_content

                    save_raw_content(kb_slug, str(source.id), content)

                    entry.status = EntryStatus.completed
                    from datetime import UTC, datetime

                    entry.fetched_at = datetime.now(UTC).replace(tzinfo=None)
                    processed += 1

                except Exception as e:
                    entry.status = EntryStatus.failed
                    logger.error("rss_entry_ingest_failed", entry_id=str(entry.id), url=entry.url, error=str(e))

    # Run wiki ingest pipelines for the created sources
    async with async_sessionmaker() as session:
        async with session.begin():
            source_repo = SourceRepository(session)

            from sqlalchemy import select

            from app.models.rss_entry import RssEntry
            from app.models.source import SourceStatus

            result = await session.execute(
                select(RssEntry).where(
                    RssEntry.feed_id == feed_id,
                    RssEntry.source_id.isnot(None),
                    RssEntry.status == EntryStatus.completed,
                )
            )
            completed_entries = list(result.scalars().all())

            for entry in completed_entries:
                if not entry.source_id:
                    continue
                source = await source_repo.get_by_id(entry.source_id)
                if not source or source.status != SourceStatus.processing:
                    continue

                try:
                    if kb.kb_type == KbType.tool_arsenal:
                        await run_tool_arsenal_pipeline(source.id, kb_slug)
                    else:
                        await run_ingest_pipeline(source.id, kb_slug)
                except Exception as e:
                    logger.error("rss_source_ingest_failed", source_id=str(source.id), error=str(e))

    logger.info("rss_entries_ingested", feed_id=feed_id, processed=processed)
    return processed
