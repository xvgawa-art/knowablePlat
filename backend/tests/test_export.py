import uuid
import zipfile

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
    resp = await client.post("/api/knowledge-bases", json={"name": f"export-{uid}", "slug": f"export-{uid}"})
    return resp.json()["slug"]


async def test_export_empty_kb(client: AsyncClient, kb_slug: str) -> None:
    resp = await client.get(f"/api/kb/{kb_slug}/wiki/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"

    zf = zipfile.ZipFile(__import__("io").BytesIO(resp.content))
    assert len(zf.namelist()) == 0


async def test_export_with_pages(client: AsyncClient, kb_slug: str) -> None:
    from app.database import async_sessionmaker
    from app.models.wiki_page import WikiPageType
    from app.repositories.knowledge_base import KnowledgeBaseRepository
    from app.repositories.wiki_page import WikiPageRepository

    async with async_sessionmaker() as session:
        async with session.begin():
            kb_repo = KnowledgeBaseRepository(session)
            kb = await kb_repo.get_by_slug(kb_slug)

            wiki_repo = WikiPageRepository(session)
            await wiki_repo.create(
                kb_id=kb.id,
                slug="test-export-page",
                title="导出测试页面",
                page_type=WikiPageType.concept,
                content="# 测试\n\n导出内容 [[other-page]]",
                source_ids=[],
                outgoing_links=["other-page"],
                incoming_links=[],
            )

    resp = await client.get(f"/api/kb/{kb_slug}/wiki/export")
    assert resp.status_code == 200

    zf = zipfile.ZipFile(__import__("io").BytesIO(resp.content))
    names = zf.namelist()
    assert "test-export-page.md" in names
    content = zf.read("test-export-page.md").decode("utf-8")
    assert "导出测试页面" in content
    assert "[[other-page]]" in content


async def test_export_kb_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/kb/nonexistent/wiki/export")
    assert resp.status_code == 404
