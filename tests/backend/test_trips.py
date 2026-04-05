"""Tests for Task 2.2-2.4: Trip CRUD, itinerary, invite, finalize.

Covers:
- Create trip
- Add itinerary items
- List trips
- Get trip detail
- Invite and join via token
- Permission check (viewer can't edit)
- Finalize flow (all members confirm)
"""

import pytest
import pytest_asyncio


async def _register_and_get_token(client, phone: str) -> str:
    """Helper: register user and return auth token."""
    await client.post("/api/auth/send-code", json={"phone": phone})
    from app.api.auth import _otp_store
    code = _otp_store.get(f"otp:{phone}")
    resp = await client.post("/api/auth/verify", json={"phone": phone, "code": code})
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(autouse=True)
async def reset_trips():
    """Reset trip store before each test."""
    from app.trips.service import _reset
    _reset()
    yield


@pytest.mark.asyncio
async def test_create_trip(client):
    token = await _register_and_get_token(client, "+886800000001")
    resp = await client.post("/api/trips", json={
        "name": "日本東京行",
        "destination": "東京",
        "start_date": "2026-07-01",
        "end_date": "2026-07-07",
        "budget": 50000,
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "日本東京行"
    assert data["destination"] == "東京"
    assert data["member_count"] == 1
    assert data["status"] == "planning"
    assert data["share_token"] != ""


@pytest.mark.asyncio
async def test_list_my_trips(client):
    token = await _register_and_get_token(client, "+886800000002")
    await client.post("/api/trips", json={
        "name": "Trip A", "destination": "A",
        "start_date": "2026-07-01", "end_date": "2026-07-05",
    }, headers=_auth(token))
    await client.post("/api/trips", json={
        "name": "Trip B", "destination": "B",
        "start_date": "2026-08-01", "end_date": "2026-08-05",
    }, headers=_auth(token))
    resp = await client.get("/api/trips", headers=_auth(token))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_add_itinerary_item(client):
    token = await _register_and_get_token(client, "+886800000003")
    trip_resp = await client.post("/api/trips", json={
        "name": "Test", "destination": "X",
        "start_date": "2026-07-01", "end_date": "2026-07-03",
    }, headers=_auth(token))
    trip_id = trip_resp.json()["id"]

    item_resp = await client.post(f"/api/trips/{trip_id}/items", json={
        "day_number": 1,
        "type": "attraction",
        "name": "淺草寺",
        "time": "10:00",
        "location": "東京淺草",
        "estimated_cost": 0,
    }, headers=_auth(token))
    assert item_resp.status_code == 201
    assert item_resp.json()["name"] == "淺草寺"
    assert item_resp.json()["type"] == "attraction"


@pytest.mark.asyncio
async def test_get_trip_detail_with_items(client):
    token = await _register_and_get_token(client, "+886800000004")
    trip_resp = await client.post("/api/trips", json={
        "name": "Detail Test", "destination": "Y",
        "start_date": "2026-07-01", "end_date": "2026-07-03",
    }, headers=_auth(token))
    trip_id = trip_resp.json()["id"]

    await client.post(f"/api/trips/{trip_id}/items", json={
        "day_number": 1, "name": "Item A", "type": "attraction",
    }, headers=_auth(token))
    await client.post(f"/api/trips/{trip_id}/items", json={
        "day_number": 1, "name": "Item B", "type": "restaurant",
    }, headers=_auth(token))

    detail = await client.get(f"/api/trips/{trip_id}", headers=_auth(token))
    assert detail.status_code == 200
    data = detail.json()
    assert len(data["items"]) == 2
    assert len(data["members"]) == 1


@pytest.mark.asyncio
async def test_invite_and_join(client):
    token1 = await _register_and_get_token(client, "+886800000005")
    token2 = await _register_and_get_token(client, "+886800000006")

    # User 1 creates trip
    trip_resp = await client.post("/api/trips", json={
        "name": "Group Trip", "destination": "Z",
        "start_date": "2026-07-01", "end_date": "2026-07-05",
    }, headers=_auth(token1))
    trip_id = trip_resp.json()["id"]
    share_token = trip_resp.json()["share_token"]

    # User 2 joins via token
    join_resp = await client.post(f"/api/trips/join/{share_token}", headers=_auth(token2))
    assert join_resp.status_code == 200

    # Verify member count
    detail = await client.get(f"/api/trips/{trip_id}", headers=_auth(token1))
    assert len(detail.json()["members"]) == 2


@pytest.mark.asyncio
async def test_viewer_cannot_edit(client):
    token1 = await _register_and_get_token(client, "+886800000007")
    token2 = await _register_and_get_token(client, "+886800000008")

    # Create trip, invite user 2
    trip_resp = await client.post("/api/trips", json={
        "name": "Permission Test", "destination": "W",
        "start_date": "2026-07-01", "end_date": "2026-07-03",
    }, headers=_auth(token1))
    trip_id = trip_resp.json()["id"]
    share_token = trip_resp.json()["share_token"]

    await client.post(f"/api/trips/join/{share_token}", headers=_auth(token2))

    # Get user2's ID
    me_resp = await client.get("/api/auth/me", headers=_auth(token2))
    user2_id = me_resp.json()["id"]

    # Set user 2 as viewer
    await client.put(
        f"/api/trips/{trip_id}/members/{user2_id}",
        json={"role": "viewer"},
        headers=_auth(token1),
    )

    # User 2 (viewer) tries to add item — should be rejected
    item_resp = await client.post(f"/api/trips/{trip_id}/items", json={
        "day_number": 1, "name": "Blocked Item", "type": "other",
    }, headers=_auth(token2))
    assert item_resp.status_code == 403


@pytest.mark.asyncio
async def test_finalize_all_members_confirm(client):
    token1 = await _register_and_get_token(client, "+886800000009")
    token2 = await _register_and_get_token(client, "+886800000010")

    trip_resp = await client.post("/api/trips", json={
        "name": "Finalize Test", "destination": "V",
        "start_date": "2026-07-01", "end_date": "2026-07-03",
    }, headers=_auth(token1))
    trip_id = trip_resp.json()["id"]
    share_token = trip_resp.json()["share_token"]

    await client.post(f"/api/trips/join/{share_token}", headers=_auth(token2))

    # User 1 confirms — not yet finalized (user 2 hasn't)
    resp1 = await client.post(f"/api/trips/{trip_id}/confirm", headers=_auth(token1))
    assert resp1.json()["status"] == "planning"

    # User 2 confirms — now all confirmed → finalized
    resp2 = await client.post(f"/api/trips/{trip_id}/confirm", headers=_auth(token2))
    assert resp2.json()["status"] == "finalized"
