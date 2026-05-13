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
async def kb_with_slug(client: AsyncClient) -> str:
    uid = uuid.uuid4().hex[:8]
    resp = await client.post("/api/knowledge-bases", json={"name": f"RSS测试-{uid}", "slug": f"rss-{uid}"})
    assert resp.status_code == 201
    return resp.json()["slug"]


async def test_create_feed(client: AsyncClient, kb_with_slug: str) -> None:
    resp = await client.post(
        f"/api/kb/{kb_with_slug}/rss",
        json={"name": "Test Feed", "url": "https://example.com/feed.xml"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Test Feed"
    assert body["url"] == "https://example.com/feed.xml"
    assert body["is_active"] is False
    assert body["poll_interval"] == 60


async def test_create_feed_with_filters(client: AsyncClient, kb_with_slug: str) -> None:
    resp = await client.post(
        f"/api/kb/{kb_with_slug}/rss",
        json={
            "name": "Filtered Feed",
            "url": "https://example.com/feed2.xml",
            "filter_keywords": ["security", "xss"],
            "filter_authors": ["alice"],
            "poll_interval": 30,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["filter_keywords"] == ["security", "xss"]
    assert body["poll_interval"] == 30


async def test_list_feeds_empty(client: AsyncClient, kb_with_slug: str) -> None:
    resp = await client.get(f"/api/kb/{kb_with_slug}/rss")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_feeds_with_data(client: AsyncClient, kb_with_slug: str) -> None:
    await client.post(
        f"/api/kb/{kb_with_slug}/rss",
        json={"name": "Feed A", "url": "https://example.com/a.xml"},
    )
    await client.post(
        f"/api/kb/{kb_with_slug}/rss",
        json={"name": "Feed B", "url": "https://example.com/b.xml"},
    )
    resp = await client.get(f"/api/kb/{kb_with_slug}/rss")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_get_feed(client: AsyncClient, kb_with_slug: str) -> None:
    create_resp = await client.post(
        f"/api/kb/{kb_with_slug}/rss",
        json={"name": "My Feed", "url": "https://example.com/feed.xml"},
    )
    feed_id = create_resp.json()["id"]

    resp = await client.get(f"/api/kb/{kb_with_slug}/rss/{feed_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "My Feed"


async def test_get_feed_not_found(client: AsyncClient, kb_with_slug: str) -> None:
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/kb/{kb_with_slug}/rss/{fake_id}")
    assert resp.status_code == 404


async def test_update_feed(client: AsyncClient, kb_with_slug: str) -> None:
    create_resp = await client.post(
        f"/api/kb/{kb_with_slug}/rss",
        json={"name": "Original", "url": "https://example.com/feed.xml"},
    )
    feed_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/kb/{kb_with_slug}/rss/{feed_id}",
        json={"name": "Updated", "poll_interval": 120},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"
    assert resp.json()["poll_interval"] == 120


async def test_update_feed_toggle_active(client: AsyncClient, kb_with_slug: str) -> None:
    create_resp = await client.post(
        f"/api/kb/{kb_with_slug}/rss",
        json={"name": "Toggle", "url": "https://example.com/feed.xml"},
    )
    feed_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/kb/{kb_with_slug}/rss/{feed_id}",
        json={"is_active": True},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True


async def test_delete_feed(client: AsyncClient, kb_with_slug: str) -> None:
    create_resp = await client.post(
        f"/api/kb/{kb_with_slug}/rss",
        json={"name": "ToDelete", "url": "https://example.com/feed.xml"},
    )
    feed_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/kb/{kb_with_slug}/rss/{feed_id}")
    assert resp.status_code == 204

    list_resp = await client.get(f"/api/kb/{kb_with_slug}/rss")
    assert len(list_resp.json()) == 0


async def test_feed_kb_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/kb/nonexistent/rss")
    assert resp.status_code == 404


async def test_list_entries_empty(client: AsyncClient, kb_with_slug: str) -> None:
    create_resp = await client.post(
        f"/api/kb/{kb_with_slug}/rss",
        json={"name": "Entries Test", "url": "https://example.com/feed.xml"},
    )
    feed_id = create_resp.json()["id"]

    resp = await client.get(f"/api/kb/{kb_with_slug}/rss/{feed_id}/entries")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_update_feed_not_found(client: AsyncClient, kb_with_slug: str) -> None:
    fake_id = str(uuid.uuid4())
    resp = await client.put(
        f"/api/kb/{kb_with_slug}/rss/{fake_id}",
        json={"name": "Ghost"},
    )
    assert resp.status_code == 404


async def test_delete_feed_not_found(client: AsyncClient, kb_with_slug: str) -> None:
    fake_id = str(uuid.uuid4())
    resp = await client.delete(f"/api/kb/{kb_with_slug}/rss/{fake_id}")
    assert resp.status_code == 404


async def test_trigger_fetch_not_found(client: AsyncClient, kb_with_slug: str) -> None:
    fake_id = str(uuid.uuid4())
    resp = await client.post(f"/api/kb/{kb_with_slug}/rss/{fake_id}/fetch", json={})
    assert resp.status_code == 404


async def test_create_feed_empty_name(client: AsyncClient, kb_with_slug: str) -> None:
    resp = await client.post(
        f"/api/kb/{kb_with_slug}/rss",
        json={"name": "", "url": "https://example.com/feed.xml"},
    )
    assert resp.status_code == 422


async def test_create_feed_missing_name(client: AsyncClient, kb_with_slug: str) -> None:
    resp = await client.post(
        f"/api/kb/{kb_with_slug}/rss",
        json={"url": "https://example.com/feed.xml"},
    )
    assert resp.status_code == 422


async def test_create_feed_invalid_poll_interval(client: AsyncClient, kb_with_slug: str) -> None:
    resp = await client.post(
        f"/api/kb/{kb_with_slug}/rss",
        json={"name": "Bad Interval", "url": "https://example.com/feed.xml", "poll_interval": 1},
    )
    assert resp.status_code == 422
