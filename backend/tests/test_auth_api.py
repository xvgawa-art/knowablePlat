import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def user_data():
    return {
        "email": f"test-{uuid.uuid4().hex[:6]}@example.com",
        "username": f"testuser_{uuid.uuid4().hex[:6]}",
        "password": "secret123",
    }


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_register(client: AsyncClient, user_data: dict) -> None:
    resp = await client.post("/api/auth/register", json=user_data)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == user_data["email"]
    assert "id" in body


async def test_register_duplicate(client: AsyncClient, user_data: dict) -> None:
    await client.post("/api/auth/register", json=user_data)
    resp = await client.post("/api/auth/register", json=user_data)
    assert resp.status_code == 409


async def test_login(client: AsyncClient, user_data: dict) -> None:
    await client.post("/api/auth/register", json=user_data)
    resp = await client.post("/api/auth/login", json={"email": user_data["email"], "password": user_data["password"]})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, user_data: dict) -> None:
    await client.post("/api/auth/register", json=user_data)
    resp = await client.post("/api/auth/login", json={"email": user_data["email"], "password": "wrong"})
    assert resp.status_code == 401


async def test_me(client: AsyncClient, user_data: dict) -> None:
    await client.post("/api/auth/register", json=user_data)
    login_resp = await client.post(
        "/api/auth/login", json={"email": user_data["email"], "password": user_data["password"]}
    )
    token = login_resp.json()["access_token"]

    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == user_data["email"]


async def test_me_no_token(client: AsyncClient) -> None:
    resp = await client.get("/api/auth/me")
    assert resp.status_code in (401, 403)


async def test_login_nonexistent_email(client: AsyncClient) -> None:
    resp = await client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "whatever"})
    assert resp.status_code == 401


async def test_register_missing_fields(client: AsyncClient) -> None:
    resp = await client.post("/api/auth/register", json={"email": "a@b.com"})
    assert resp.status_code == 422
