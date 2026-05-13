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
async def seeded_notifications(client: AsyncClient) -> dict:
    uid = uuid.uuid4().hex[:8]
    resp = await client.post("/api/knowledge-bases", json={"name": f"全局通知测试-{uid}", "slug": f"gn-test-{uid}"})
    kb_slug = resp.json()["slug"]

    from app.database import async_sessionmaker
    from app.models.notification import Notification, TriggerType
    from app.models.source import Source, SourceStatus
    from app.repositories.knowledge_base import KnowledgeBaseRepository

    source_ids = []
    async with async_sessionmaker() as session:
        async with session.begin():
            kb_repo = KnowledgeBaseRepository(session)
            kb = await kb_repo.get_by_slug(kb_slug)

            for i in range(3):
                source = Source(kb_id=kb.id, url=f"https://example.com/gn-test-{i}", status=SourceStatus.completed)
                session.add(source)
                await session.flush()
                source_ids.append(str(source.id))

                notif = Notification(
                    kb_id=kb.id,
                    source_id=source.id,
                    trigger_type=TriggerType.manual if i < 2 else TriggerType.rss,
                    title=f"全局测试通知 {i}",
                    summary=f"摘要 {i}",
                    is_read=(i == 0),
                )
                session.add(notif)

    return {"kb_slug": kb_slug, "source_ids": source_ids}


async def test_list_all_notifications_returns_list(client: AsyncClient) -> None:
    resp = await client.get("/api/notifications")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "unread_count" in body


async def test_list_all_notifications_with_data(client: AsyncClient, seeded_notifications: dict) -> None:
    resp = await client.get("/api/notifications")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) >= 3
    assert body["unread_count"] >= 2


async def test_list_unread_only(client: AsyncClient, seeded_notifications: dict) -> None:
    resp = await client.get("/api/notifications", params={"unread": "true"})
    assert resp.status_code == 200
    body = resp.json()
    assert all(item["is_read"] is False for item in body["items"])


async def test_get_unread_count(client: AsyncClient, seeded_notifications: dict) -> None:
    resp = await client.get("/api/notifications/unread-count")
    assert resp.status_code == 200
    assert resp.json()["unread_count"] >= 2


async def test_get_notification_detail(client: AsyncClient, seeded_notifications: dict) -> None:
    list_resp = await client.get("/api/notifications")
    notif_id = list_resp.json()["items"][0]["id"]

    resp = await client.get(f"/api/notifications/{notif_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == notif_id


async def test_get_notification_not_found(client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/notifications/{fake_id}")
    assert resp.status_code == 404


async def test_mark_notification_read(client: AsyncClient, seeded_notifications: dict) -> None:
    list_resp = await client.get("/api/notifications", params={"unread": "true"})
    notif_id = list_resp.json()["items"][0]["id"]

    resp = await client.put(f"/api/notifications/{notif_id}/read")
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True


async def test_mark_all_read(client: AsyncClient, seeded_notifications: dict) -> None:
    resp = await client.put("/api/notifications/read-all")
    assert resp.status_code == 204

    count_resp = await client.get("/api/notifications/unread-count")
    assert count_resp.json()["unread_count"] == 0
