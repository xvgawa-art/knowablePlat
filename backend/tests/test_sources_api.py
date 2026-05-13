import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def kb_slug(client: AsyncClient) -> str:
    uid = uuid.uuid4().hex[:8]
    resp = await client.post("/api/knowledge-bases", json={"name": f"测试-{uid}", "slug": f"test-{uid}"})
    return resp.json()["slug"]


async def test_create_source(client: AsyncClient, kb_slug: str) -> None:
    resp = await client.post(f"/api/kb/{kb_slug}/sources", json={"url": "https://example.com/article"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["url"] == "https://example.com/article"
    assert body["status"] == "processing"


async def test_create_duplicate_source(client: AsyncClient, kb_slug: str) -> None:
    url = "https://example.com/dup-test"
    await client.post(f"/api/kb/{kb_slug}/sources", json={"url": url})
    resp = await client.post(f"/api/kb/{kb_slug}/sources", json={"url": url})
    assert resp.status_code == 409


async def test_list_sources(client: AsyncClient, kb_slug: str) -> None:
    await client.post(f"/api/kb/{kb_slug}/sources", json={"url": "https://example.com/1"})
    resp = await client.get(f"/api/kb/{kb_slug}/sources")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_get_source_detail(client: AsyncClient, kb_slug: str) -> None:
    create_resp = await client.post(f"/api/kb/{kb_slug}/sources", json={"url": "https://example.com/detail"})
    source_id = create_resp.json()["id"]

    resp = await client.get(f"/api/kb/{kb_slug}/sources/{source_id}")
    assert resp.status_code == 200
    assert "raw_content" in resp.json()


async def test_get_source_not_found(client: AsyncClient, kb_slug: str) -> None:
    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/kb/{kb_slug}/sources/{fake_id}")
    assert resp.status_code == 404


async def test_delete_source(client: AsyncClient, kb_slug: str) -> None:
    create_resp = await client.post(f"/api/kb/{kb_slug}/sources", json={"url": "https://example.com/del"})
    source_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/kb/{kb_slug}/sources/{source_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/kb/{kb_slug}/sources/{source_id}")
    assert resp.status_code == 404


async def test_source_kb_not_found(client: AsyncClient) -> None:
    resp = await client.post("/api/kb/nonexistent/sources", json={"url": "https://example.com"})
    assert resp.status_code == 404


async def test_batch_create_sources(client: AsyncClient, kb_slug: str) -> None:
    urls = [
        "https://example.com/batch-1",
        "https://example.com/batch-2",
        "https://example.com/batch-3",
    ]
    resp = await client.post(f"/api/kb/{kb_slug}/sources/batch", json={"urls": urls})
    assert resp.status_code == 201
    sources = resp.json()
    assert len(sources) == 3
    assert all(s["status"] == "processing" for s in sources)


async def test_batch_create_with_duplicate(client: AsyncClient, kb_slug: str) -> None:
    await client.post(f"/api/kb/{kb_slug}/sources", json={"url": "https://example.com/batch-dup"})
    resp = await client.post(
        f"/api/kb/{kb_slug}/sources/batch",
        json={"urls": ["https://example.com/batch-dup", "https://example.com/batch-new"]},
    )
    assert resp.status_code == 201
    sources = resp.json()
    assert len(sources) == 2


async def test_retry_failed_source(client: AsyncClient, kb_slug: str) -> None:
    from unittest.mock import patch

    from app.database import async_sessionmaker
    from app.models.source import SourceStatus
    from app.repositories.knowledge_base import KnowledgeBaseRepository
    from app.repositories.source import SourceRepository

    # Create a source and mark it as failed
    async with async_sessionmaker() as session:
        async with session.begin():
            kb_repo = KnowledgeBaseRepository(session)
            kb = await kb_repo.get_by_slug(kb_slug)
            source_repo = SourceRepository(session)
            source = await source_repo.create(
                kb_id=kb.id, url="https://example.com/fail-test", status=SourceStatus.failed
            )
            source_id = source.id

    with patch("app.api.sources._ingest_source"):
        resp = await client.post(f"/api/kb/{kb_slug}/sources/{source_id}/retry")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "processing"


async def test_retry_non_failed_source(client: AsyncClient, kb_slug: str) -> None:
    from app.database import async_sessionmaker
    from app.repositories.knowledge_base import KnowledgeBaseRepository
    from app.repositories.source import SourceRepository

    async with async_sessionmaker() as session:
        async with session.begin():
            kb_repo = KnowledgeBaseRepository(session)
            kb = await kb_repo.get_by_slug(kb_slug)
            source_repo = SourceRepository(session)
            source = await source_repo.create(kb_id=kb.id, url="https://example.com/completed-test")
            source_id = source.id

    resp = await client.post(f"/api/kb/{kb_slug}/sources/{source_id}/retry")
    assert resp.status_code == 400


async def test_retry_not_found(client: AsyncClient, kb_slug: str) -> None:
    resp = await client.post(f"/api/kb/{kb_slug}/sources/{uuid.uuid4()}/retry")
    assert resp.status_code == 404
