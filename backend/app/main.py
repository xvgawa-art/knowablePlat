from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import ensure_dirs


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dirs()
    yield


app = FastAPI(title="KnowablePlat", version="0.1.0", lifespan=lifespan)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
