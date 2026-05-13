from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.generate import router as generate_router
from app.api.global_notifications import router as global_notif_router
from app.api.knowledge_bases import router as kb_router
from app.api.notifications import router as notif_router
from app.api.rss import router as rss_router
from app.api.sources import router as sources_router
from app.api.wiki import router as wiki_router
from app.config import ensure_dirs
from app.database import async_sessionmaker


async def _init_tool_arsenal() -> None:
    from app.repositories.knowledge_base import KnowledgeBaseRepository

    async with async_sessionmaker() as session:
        async with session.begin():
            repo = KnowledgeBaseRepository(session)
            await repo.ensure_tool_arsenal()


async def _poll_all_feeds() -> None:
    """Scheduled task: poll all active RSS feeds."""
    from app.repositories.rss_feed import RssFeedRepository

    async with async_sessionmaker() as session:
        async with session.begin():
            repo = RssFeedRepository(session)
            feeds = await repo.list_active()

    for feed in feeds:
        try:
            from app.services.rss_fetcher import poll_feed

            await poll_feed(str(feed.id), "")
        except Exception as e:
            import structlog

            structlog.get_logger().error("rss_poll_feed_error", feed_id=str(feed.id), error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    import structlog

    logger = structlog.get_logger()
    ensure_dirs()
    await _init_tool_arsenal()

    # Start RSS scheduler
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler()
    scheduler.add_job(_poll_all_feeds, "interval", minutes=60, id="rss_poll", replace_existing=True)
    scheduler.start()
    logger.info("rss_scheduler_started", interval_minutes=60)

    yield
    scheduler.shutdown()


app = FastAPI(title="KnowablePlat", version="0.1.0", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(kb_router)
app.include_router(sources_router)
app.include_router(wiki_router)
app.include_router(notif_router)
app.include_router(global_notif_router)
app.include_router(rss_router)
app.include_router(generate_router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
