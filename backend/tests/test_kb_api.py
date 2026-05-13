import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def kb_data():
    uid = uuid.uuid4().hex[:8]
    return {"name": f"测试知识库-{uid}", "slug": f"test-kb-{uid}", "description": "测试知识库"}


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    uid = uuid.uuid4().hex[:8]
    await client.post("/api/auth/register", json={"email": f"test-{uid}@example.com", "username": f"user-{uid}", "password": "password123"})
    login_resp = await client.post("/api/auth/login", json={"email": f"test-{uid}@example.com", "password": "password123"})
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_health_check(client: AsyncClient) -> None:
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_create_kb(client: AsyncClient, kb_data: dict) -> None:
    resp = await client.post("/api/knowledge-bases", json=kb_data)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == kb_data["name"]
    assert body["slug"] == kb_data["slug"]
    assert body["kb_type"] == "knowledge"
    assert body["is_system"] is False


async def test_create_kb_duplicate_slug(client: AsyncClient, kb_data: dict) -> None:
    await client.post("/api/knowledge-bases", json=kb_data)
    resp = await client.post("/api/knowledge-bases", json=kb_data)
    assert resp.status_code == 409


async def test_list_kbs(client: AsyncClient, kb_data: dict) -> None:
    await client.post("/api/knowledge-bases", json=kb_data)
    resp = await client.get("/api/knowledge-bases")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1


async def test_get_kb_by_slug(client: AsyncClient, kb_data: dict) -> None:
    create_resp = await client.post("/api/knowledge-bases", json=kb_data)
    slug = create_resp.json()["slug"]

    resp = await client.get(f"/api/knowledge-bases/{slug}")
    assert resp.status_code == 200
    assert resp.json()["slug"] == slug


async def test_get_kb_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/knowledge-bases/nonexistent")
    assert resp.status_code == 404


async def test_update_kb(client: AsyncClient, kb_data: dict, auth_headers: dict[str, str]) -> None:
    create_resp = await client.post("/api/knowledge-bases", json=kb_data, headers=auth_headers)
    slug = create_resp.json()["slug"]

    new_name = f"更新后-{uuid.uuid4().hex[:6]}"
    resp = await client.put(f"/api/knowledge-bases/{slug}", json={"name": new_name}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == new_name


async def test_delete_kb(client: AsyncClient, kb_data: dict, auth_headers: dict[str, str]) -> None:
    create_resp = await client.post("/api/knowledge-bases", json=kb_data, headers=auth_headers)
    slug = create_resp.json()["slug"]

    resp = await client.delete(f"/api/knowledge-bases/{slug}", headers=auth_headers)
    assert resp.status_code == 204

    resp = await client.get(f"/api/knowledge-bases/{slug}")
    assert resp.status_code == 404


async def test_cannot_delete_tool_arsenal(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.delete("/api/knowledge-bases/tool-arsenal", headers=auth_headers)
    assert resp.status_code == 403


async def test_cannot_update_tool_arsenal(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.put("/api/knowledge-bases/tool-arsenal", json={"name": "hacked"}, headers=auth_headers)
    assert resp.status_code == 403


async def test_tool_arsenal_auto_created(client: AsyncClient) -> None:
    resp = await client.get("/api/knowledge-bases/tool-arsenal")
    assert resp.status_code == 200
    body = resp.json()
    assert body["kb_type"] == "tool_arsenal"
    assert body["is_system"] is True
