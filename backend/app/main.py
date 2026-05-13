from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.knowledge_bases import router as kb_router
from app.api.sources import router as sources_router
from app.config import ensure_dirs
from app.database import async_sessionmaker


async def _init_tool_arsenal() -> None:
    from app.repositories.knowledge_base import KnowledgeBaseRepository

    async with async_sessionmaker() as session:
        async with session.begin():
            repo = KnowledgeBaseRepository(session)
            await repo.ensure_tool_arsenal()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dirs()
    await _init_tool_arsenal()
    yield


app = FastAPI(title="KnowablePlat", version="0.1.0", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(kb_router)
app.include_router(sources_router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
