"""Tests for Phase 3: Comments, edit history, finalize flow.

Task 3.2: Comments on itinerary items
Task 3.3: Edit history
Task 3.4: Full finalize flow (initiate → confirm → lock → unlock)
"""

import pytest
import pytest_asyncio


async def _register(client, phone: str) -> str:
    await client.post("/api/auth/send-code", json={"phone": phone})
    from app.api.auth import _otp_store
    code = _otp_store.get(f"otp:{phone}")
    resp = await client.post("/api/auth/verify", json={"phone": phone, "code": code})
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(autouse=True)
async def reset_stores():
    from app.trips.service import _reset
    from app.trips.comments import _reset as _reset_comments
    _reset()
    _reset_comments()
    yield


async def _create_trip_with_item(client, token):
    """Helper: create a trip with one item, return (trip_id, item_id)."""
    trip_resp = await client.post("/api/trips", json={
        "name": "Phase3 Test", "destination": "Tokyo",
        "start_date": "2026-07-01", "end_date": "2026-07-05",
    }, headers=_auth(token))
    trip_id = trip_resp.json()["id"]

    item_resp = await client.post(f"/api/trips/{trip_id}/items", json={
        "day_number": 1, "name": "淺草寺", "type": "attraction",
    }, headers=_auth(token))
    item_id = item_resp.json()["id"]
    return trip_id, item_id


# --- Task 3.2: Comments ---

@pytest.mark.asyncio
async def test_add_comment_to_item(client):
    token = await _register(client, "+886700000001")
    trip_id, item_id = await _create_trip_with_item(client, token)

    resp = await client.post(
        f"/api/trips/{trip_id}/items/{item_id}/comments",
        json={"text": "這個景點要早上去比較好！"},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["text"] == "這個景點要早上去比較好！"
    assert data["item_id"] == item_id


@pytest.mark.asyncio
async def test_list_comments(client):
    token = await _register(client, "+886700000002")
    trip_id, item_id = await _create_trip_with_item(client, token)

    await client.post(f"/api/trips/{trip_id}/items/{item_id}/comments",
                      json={"text": "Comment 1"}, headers=_auth(token))
    await client.post(f"/api/trips/{trip_id}/items/{item_id}/comments",
                      json={"text": "Comment 2"}, headers=_auth(token))

    resp = await client.get(f"/api/trips/{trip_id}/items/{item_id}/comments",
                            headers=_auth(token))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# --- Task 3.3: Edit history ---

@pytest.mark.asyncio
async def test_edit_history_records_comments(client):
    token = await _register(client, "+886700000003")
    trip_id, item_id = await _create_trip_with_item(client, token)

    await client.post(f"/api/trips/{trip_id}/items/{item_id}/comments",
                      json={"text": "Test comment"}, headers=_auth(token))

    resp = await client.get(f"/api/trips/{trip_id}/history", headers=_auth(token))
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) >= 1
    assert any(h["action"] == "add_comment" for h in history)


# --- Task 3.4: Finalize flow ---

@pytest.mark.asyncio
async def test_owner_initiates_finalize(client):
    token = await _register(client, "+886700000004")
    trip_id, _ = await _create_trip_with_item(client, token)

    resp = await client.post(f"/api/trips/{trip_id}/finalize", headers=_auth(token))
    assert resp.status_code == 200
    # Owner is auto-confirmed, and they're the only member → finalized
    assert resp.json()["status"] == "finalized"


@pytest.mark.asyncio
async def test_finalize_requires_all_members(client):
    token1 = await _register(client, "+886700000005")
    token2 = await _register(client, "+886700000006")

    trip_resp = await client.post("/api/trips", json={
        "name": "Group Finalize", "destination": "Paris",
        "start_date": "2026-08-01", "end_date": "2026-08-10",
    }, headers=_auth(token1))
    trip_id = trip_resp.json()["id"]
    share_token = trip_resp.json()["share_token"]

    # User 2 joins
    await client.post(f"/api/trips/join/{share_token}", headers=_auth(token2))

    # Owner initiates finalize — not yet done (user 2 hasn't confirmed)
    resp = await client.post(f"/api/trips/{trip_id}/finalize", headers=_auth(token1))
    assert resp.json()["status"] == "planning"
    assert resp.json()["pending_count"] == 1

    # User 2 confirms
    resp2 = await client.post(f"/api/trips/{trip_id}/confirm", headers=_auth(token2))
    assert resp2.json()["status"] == "finalized"


@pytest.mark.asyncio
async def test_non_owner_cannot_initiate_finalize(client):
    token1 = await _register(client, "+886700000007")
    token2 = await _register(client, "+886700000008")

    trip_resp = await client.post("/api/trips", json={
        "name": "Permission Test", "destination": "London",
        "start_date": "2026-09-01", "end_date": "2026-09-05",
    }, headers=_auth(token1))
    trip_id = trip_resp.json()["id"]
    share_token = trip_resp.json()["share_token"]
    await client.post(f"/api/trips/join/{share_token}", headers=_auth(token2))

    # User 2 (non-owner) tries to initiate finalize
    resp = await client.post(f"/api/trips/{trip_id}/finalize", headers=_auth(token2))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unlock_finalized_trip(client):
    token = await _register(client, "+886700000009")
    trip_id, _ = await _create_trip_with_item(client, token)

    # Finalize
    await client.post(f"/api/trips/{trip_id}/finalize", headers=_auth(token))

    # Unlock
    resp = await client.post(f"/api/trips/{trip_id}/unlock", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "planning"

    # Verify trip is back to planning
    detail = await client.get(f"/api/trips/{trip_id}", headers=_auth(token))
    assert detail.json()["status"] == "planning"


@pytest.mark.asyncio
async def test_finalize_records_history(client):
    token = await _register(client, "+886700000010")
    trip_id, _ = await _create_trip_with_item(client, token)

    await client.post(f"/api/trips/{trip_id}/finalize", headers=_auth(token))

    resp = await client.get(f"/api/trips/{trip_id}/history", headers=_auth(token))
    history = resp.json()
    assert any(h["action"] == "finalize" for h in history)
