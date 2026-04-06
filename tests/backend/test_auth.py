"""Tests for auth — database-backed."""

import pytest

from app.auth.service import _otp_store


@pytest.mark.asyncio
async def test_send_code(client):
    resp = await client.post("/api/auth/send-code", json={"phone": "+886912345678"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_verify_code_and_get_token(client):
    await client.post("/api/auth/send-code", json={"phone": "+886900000001"})
    code = _otp_store.get("otp:+886900000001")
    assert code is not None

    resp = await client.post("/api/auth/verify", json={"phone": "+886900000001", "code": code})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["is_new_user"] is True


@pytest.mark.asyncio
async def test_verify_wrong_code_rejected(client):
    await client.post("/api/auth/send-code", json={"phone": "+886900000002"})
    resp = await client.post("/api/auth/verify", json={"phone": "+886900000002", "code": "000000"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_existing_user_not_new(client):
    await client.post("/api/auth/send-code", json={"phone": "+886900000003"})
    code1 = _otp_store.get("otp:+886900000003")
    resp1 = await client.post("/api/auth/verify", json={"phone": "+886900000003", "code": code1})
    assert resp1.json()["is_new_user"] is True

    await client.post("/api/auth/send-code", json={"phone": "+886900000003"})
    code2 = _otp_store.get("otp:+886900000003")
    resp2 = await client.post("/api/auth/verify", json={"phone": "+886900000003", "code": code2})
    assert resp2.json()["is_new_user"] is False


@pytest.mark.asyncio
async def test_get_profile_requires_auth(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_profile_with_token(client):
    token = await _register(client, "+886900000004")
    resp = await client.get("/api/auth/me", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["phone"] == "+886900000004"


@pytest.mark.asyncio
async def test_update_profile(client):
    token = await _register(client, "+886900000005")
    resp = await client.put("/api/auth/me", json={"name": "Amber"}, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["name"] == "Amber"


# --- Helpers ---

async def _register(client, phone: str) -> str:
    await client.post("/api/auth/send-code", json={"phone": phone})
    code = _otp_store.get(f"otp:{phone}")
    resp = await client.post("/api/auth/verify", json={"phone": phone, "code": code})
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
