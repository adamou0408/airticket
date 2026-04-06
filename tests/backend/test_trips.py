"""Tests for trips — database-backed."""

import pytest

from app.auth.service import _otp_store


async def _register(client, phone: str) -> str:
    await client.post("/api/auth/send-code", json={"phone": phone})
    code = _otp_store.get(f"otp:{phone}")
    resp = await client.post("/api/auth/verify", json={"phone": phone, "code": code})
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_trip(client):
    token = await _register(client, "+886800000001")
    resp = await client.post("/api/trips", json={
        "name": "日本東京行", "destination": "東京",
        "start_date": "2026-07-01", "end_date": "2026-07-07", "budget": 50000,
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "日本東京行"
    assert data["member_count"] == 1
    assert data["status"] == "planning"


@pytest.mark.asyncio
async def test_list_my_trips(client):
    token = await _register(client, "+886800000002")
    await client.post("/api/trips", json={"name": "A", "destination": "A", "start_date": "2026-07-01", "end_date": "2026-07-05"}, headers=_auth(token))
    await client.post("/api/trips", json={"name": "B", "destination": "B", "start_date": "2026-08-01", "end_date": "2026-08-05"}, headers=_auth(token))
    resp = await client.get("/api/trips", headers=_auth(token))
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_add_itinerary_item(client):
    token = await _register(client, "+886800000003")
    trip = await client.post("/api/trips", json={"name": "Test", "destination": "X", "start_date": "2026-07-01", "end_date": "2026-07-03"}, headers=_auth(token))
    trip_id = trip.json()["id"]
    item = await client.post(f"/api/trips/{trip_id}/items", json={"day_number": 1, "type": "attraction", "name": "淺草寺"}, headers=_auth(token))
    assert item.status_code == 201
    assert item.json()["name"] == "淺草寺"


@pytest.mark.asyncio
async def test_get_trip_detail_with_items(client):
    token = await _register(client, "+886800000004")
    trip = await client.post("/api/trips", json={"name": "Detail", "destination": "Y", "start_date": "2026-07-01", "end_date": "2026-07-03"}, headers=_auth(token))
    trip_id = trip.json()["id"]
    await client.post(f"/api/trips/{trip_id}/items", json={"day_number": 1, "name": "A", "type": "attraction"}, headers=_auth(token))
    await client.post(f"/api/trips/{trip_id}/items", json={"day_number": 1, "name": "B", "type": "restaurant"}, headers=_auth(token))
    detail = await client.get(f"/api/trips/{trip_id}", headers=_auth(token))
    assert len(detail.json()["items"]) == 2
    assert len(detail.json()["members"]) == 1


@pytest.mark.asyncio
async def test_invite_and_join(client):
    token1 = await _register(client, "+886800000005")
    token2 = await _register(client, "+886800000006")
    trip = await client.post("/api/trips", json={"name": "Group", "destination": "Z", "start_date": "2026-07-01", "end_date": "2026-07-05"}, headers=_auth(token1))
    share_token = trip.json()["share_token"]
    await client.post(f"/api/trips/join/{share_token}", headers=_auth(token2))
    detail = await client.get(f"/api/trips/{trip.json()['id']}", headers=_auth(token1))
    assert len(detail.json()["members"]) == 2


@pytest.mark.asyncio
async def test_viewer_cannot_edit(client):
    token1 = await _register(client, "+886800000007")
    token2 = await _register(client, "+886800000008")
    trip = await client.post("/api/trips", json={"name": "Perm", "destination": "W", "start_date": "2026-07-01", "end_date": "2026-07-03"}, headers=_auth(token1))
    trip_id = trip.json()["id"]
    await client.post(f"/api/trips/join/{trip.json()['share_token']}", headers=_auth(token2))
    me = await client.get("/api/auth/me", headers=_auth(token2))
    uid2 = me.json()["id"]
    await client.put(f"/api/trips/{trip_id}/members/{uid2}", json={"role": "viewer"}, headers=_auth(token1))
    item = await client.post(f"/api/trips/{trip_id}/items", json={"day_number": 1, "name": "Blocked", "type": "other"}, headers=_auth(token2))
    assert item.status_code == 403


@pytest.mark.asyncio
async def test_finalize_all_members_confirm(client):
    token1 = await _register(client, "+886800000009")
    token2 = await _register(client, "+886800000010")
    trip = await client.post("/api/trips", json={"name": "Final", "destination": "V", "start_date": "2026-07-01", "end_date": "2026-07-03"}, headers=_auth(token1))
    trip_id = trip.json()["id"]
    await client.post(f"/api/trips/join/{trip.json()['share_token']}", headers=_auth(token2))
    r1 = await client.post(f"/api/trips/{trip_id}/confirm", headers=_auth(token1))
    assert r1.json()["status"] == "planning"
    r2 = await client.post(f"/api/trips/{trip_id}/confirm", headers=_auth(token2))
    assert r2.json()["status"] == "finalized"
