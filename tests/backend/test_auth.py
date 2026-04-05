"""Tests for Task 2.1: User authentication service.

Covers:
- Send OTP code
- Verify OTP and get JWT
- Auto-register new users
- JWT-protected endpoints (/me)
- Invalid OTP rejection
"""

import pytest


@pytest.mark.asyncio
async def test_send_code(client):
    resp = await client.post("/api/auth/send-code", json={"phone": "+886912345678"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "驗證碼已發送"


@pytest.mark.asyncio
async def test_verify_code_and_get_token(client):
    # Send code first
    await client.post("/api/auth/send-code", json={"phone": "+886900000001"})

    # Get the OTP from the fake store
    from app.api.auth import _otp_store
    code = _otp_store.get("otp:+886900000001")
    assert code is not None

    # Verify
    resp = await client.post("/api/auth/verify", json={
        "phone": "+886900000001",
        "code": code,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["is_new_user"] is True
    assert data["user_id"] > 0


@pytest.mark.asyncio
async def test_verify_wrong_code_rejected(client):
    await client.post("/api/auth/send-code", json={"phone": "+886900000002"})
    resp = await client.post("/api/auth/verify", json={
        "phone": "+886900000002",
        "code": "000000",  # wrong code
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_existing_user_not_new(client):
    # First registration
    await client.post("/api/auth/send-code", json={"phone": "+886900000003"})
    from app.api.auth import _otp_store
    code1 = _otp_store.get("otp:+886900000003")
    resp1 = await client.post("/api/auth/verify", json={"phone": "+886900000003", "code": code1})
    assert resp1.json()["is_new_user"] is True
    user_id = resp1.json()["user_id"]

    # Second login — same phone
    await client.post("/api/auth/send-code", json={"phone": "+886900000003"})
    code2 = _otp_store.get("otp:+886900000003")
    resp2 = await client.post("/api/auth/verify", json={"phone": "+886900000003", "code": code2})
    assert resp2.json()["is_new_user"] is False
    assert resp2.json()["user_id"] == user_id


@pytest.mark.asyncio
async def test_get_profile_requires_auth(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_profile_with_token(client):
    # Register and get token
    await client.post("/api/auth/send-code", json={"phone": "+886900000004"})
    from app.api.auth import _otp_store
    code = _otp_store.get("otp:+886900000004")
    verify_resp = await client.post("/api/auth/verify", json={"phone": "+886900000004", "code": code})
    token = verify_resp.json()["access_token"]

    # Get profile
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["phone"] == "+886900000004"


@pytest.mark.asyncio
async def test_update_profile(client):
    # Register
    await client.post("/api/auth/send-code", json={"phone": "+886900000005"})
    from app.api.auth import _otp_store
    code = _otp_store.get("otp:+886900000005")
    verify_resp = await client.post("/api/auth/verify", json={"phone": "+886900000005", "code": code})
    token = verify_resp.json()["access_token"]

    # Update name
    resp = await client.put(
        "/api/auth/me",
        json={"name": "Amber"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Amber"
