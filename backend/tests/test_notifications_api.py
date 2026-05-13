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
async def kb_with_notification(client: AsyncClient) -> dict:
    uid = uuid.uuid4().hex[:8]
    resp = await client.post("/api/knowledge-bases", json={"name": f"测试-{uid}", "slug": f"test-{uid}"})
    kb_slug = resp.json()["slug"]

    from app.database import async_sessionmaker
    from app.models.notification import Notification, TriggerType

    async with async_sessionmaker() as session:
        async with session.begin():
            from app.repositories.knowledge_base import KnowledgeBaseRepository

            kb_repo = KnowledgeBaseRepository(session)
            kb = await kb_repo.get_by_slug(kb_slug)

            from app.models.source import Source, SourceStatus

            source = Source(kb_id=kb.id, url="https://example.com/test", status=SourceStatus.completed)
            session.add(source)
            await session.flush()

            notif = Notification(
                kb_id=kb.id,
                source_id=source.id,
                trigger_type=TriggerType.manual,
                title="测试通知",
                summary="这是一条测试通知",
            )
            session.add(notif)

    return {"kb_slug": kb_slug, "source_id": str(source.id)}


async def test_list_notifications_empty(client: AsyncClient) -> None:
    uid = uuid.uuid4().hex[:8]
    resp = await client.post("/api/knowledge-bases", json={"name": f"测试-{uid}", "slug": f"test-{uid}"})
    kb_slug = resp.json()["slug"]

    resp = await client.get(f"/api/kb/{kb_slug}/notifications")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["unread_count"] == 0


async def test_list_notifications_with_data(client: AsyncClient, kb_with_notification: dict) -> None:
    resp = await client.get(f"/api/kb/{kb_with_notification['kb_slug']}/notifications")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) >= 1
    assert body["unread_count"] >= 1
    assert body["items"][0]["title"] == "测试通知"


async def test_mark_notification_read(client: AsyncClient, kb_with_notification: dict) -> None:
    list_resp = await client.get(f"/api/kb/{kb_with_notification['kb_slug']}/notifications")
    notif_id = list_resp.json()["items"][0]["id"]

    resp = await client.put(f"/api/kb/{kb_with_notification['kb_slug']}/notifications/{notif_id}/read")
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True


async def test_mark_all_read(client: AsyncClient, kb_with_notification: dict) -> None:
    resp = await client.put(f"/api/kb/{kb_with_notification['kb_slug']}/notifications/read-all")
    assert resp.status_code == 204

    list_resp = await client.get(f"/api/kb/{kb_with_notification['kb_slug']}/notifications")
    assert list_resp.json()["unread_count"] == 0


async def test_notifications_kb_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/kb/nonexistent/notifications")
    assert resp.status_code == 404
