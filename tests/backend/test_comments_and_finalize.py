"""Tests for Phase 3: Comments, edit history, finalize flow — database-backed."""

import pytest

from app.auth.service import _otp_store


async def _register(client, phone: str) -> str:
    await client.post("/api/auth/send-code", json={"phone": phone})
    code = _otp_store.get(f"otp:{phone}")
    resp = await client.post("/api/auth/verify", json={"phone": phone, "code": code})
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_trip_with_item(client, token):
    trip = await client.post("/api/trips", json={
        "name": "Phase3", "destination": "Tokyo",
        "start_date": "2026-07-01", "end_date": "2026-07-05",
    }, headers=_auth(token))
    trip_id = trip.json()["id"]
    item = await client.post(f"/api/trips/{trip_id}/items", json={"day_number": 1, "name": "淺草寺", "type": "attraction"}, headers=_auth(token))
    return trip_id, item.json()["id"]


@pytest.mark.asyncio
async def test_add_comment(client):
    token = await _register(client, "+886700000001")
    trip_id, item_id = await _create_trip_with_item(client, token)
    resp = await client.post(f"/api/trips/{trip_id}/items/{item_id}/comments", json={"text": "早上去比較好"}, headers=_auth(token))
    assert resp.status_code == 201
    assert resp.json()["text"] == "早上去比較好"


@pytest.mark.asyncio
async def test_list_comments(client):
    token = await _register(client, "+886700000002")
    trip_id, item_id = await _create_trip_with_item(client, token)
    await client.post(f"/api/trips/{trip_id}/items/{item_id}/comments", json={"text": "A"}, headers=_auth(token))
    await client.post(f"/api/trips/{trip_id}/items/{item_id}/comments", json={"text": "B"}, headers=_auth(token))
    resp = await client.get(f"/api/trips/{trip_id}/items/{item_id}/comments", headers=_auth(token))
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_edit_history(client):
    token = await _register(client, "+886700000003")
    trip_id, item_id = await _create_trip_with_item(client, token)
    await client.post(f"/api/trips/{trip_id}/items/{item_id}/comments", json={"text": "Test"}, headers=_auth(token))
    resp = await client.get(f"/api/trips/{trip_id}/history", headers=_auth(token))
    assert any(h["action"] == "add_comment" for h in resp.json())


@pytest.mark.asyncio
async def test_finalize_single_owner(client):
    token = await _register(client, "+886700000004")
    trip_id, _ = await _create_trip_with_item(client, token)
    resp = await client.post(f"/api/trips/{trip_id}/finalize", headers=_auth(token))
    assert resp.json()["status"] == "finalized"


@pytest.mark.asyncio
async def test_finalize_requires_all(client):
    token1 = await _register(client, "+886700000005")
    token2 = await _register(client, "+886700000006")
    trip = await client.post("/api/trips", json={"name": "Group", "destination": "Paris", "start_date": "2026-08-01", "end_date": "2026-08-10"}, headers=_auth(token1))
    trip_id = trip.json()["id"]
    await client.post(f"/api/trips/join/{trip.json()['share_token']}", headers=_auth(token2))
    r1 = await client.post(f"/api/trips/{trip_id}/finalize", headers=_auth(token1))
    assert r1.json()["status"] == "planning"
    r2 = await client.post(f"/api/trips/{trip_id}/confirm", headers=_auth(token2))
    assert r2.json()["status"] == "finalized"


@pytest.mark.asyncio
async def test_unlock(client):
    token = await _register(client, "+886700000009")
    trip_id, _ = await _create_trip_with_item(client, token)
    await client.post(f"/api/trips/{trip_id}/finalize", headers=_auth(token))
    resp = await client.post(f"/api/trips/{trip_id}/unlock", headers=_auth(token))
    assert resp.json()["status"] == "planning"
