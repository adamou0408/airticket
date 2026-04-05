"""Tests for Phase 5: Share and export.

Task 5.1: Trip export (text + JSON)
Task 5.2: Read-only share link (no auth)
Task 5.3: Settlement export
"""

import pytest
import pytest_asyncio


async def _register(client, phone: str) -> tuple[str, int]:
    await client.post("/api/auth/send-code", json={"phone": phone})
    from app.api.auth import _otp_store
    code = _otp_store.get(f"otp:{phone}")
    resp = await client.post("/api/auth/verify", json={"phone": phone, "code": code})
    data = resp.json()
    return data["access_token"], data["user_id"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(autouse=True)
async def reset_stores():
    from app.trips.service import _reset as reset_trips
    from app.trips.comments import _reset as reset_comments
    from app.expenses.service import _reset as reset_expenses
    reset_trips()
    reset_comments()
    reset_expenses()
    yield


async def _setup_trip_with_items(client):
    """Helper: create trip with items and expenses."""
    token, uid = await _register(client, "+886500000001")

    trip_resp = await client.post("/api/trips", json={
        "name": "東京家族旅行", "destination": "東京",
        "start_date": "2026-07-01", "end_date": "2026-07-03",
        "budget": 50000,
    }, headers=_auth(token))
    trip_id = trip_resp.json()["id"]
    share_token = trip_resp.json()["share_token"]

    # Add items
    await client.post(f"/api/trips/{trip_id}/items", json={
        "day_number": 1, "name": "淺草寺", "type": "attraction",
        "time": "10:00", "location": "東京淺草", "estimated_cost": 0,
    }, headers=_auth(token))
    await client.post(f"/api/trips/{trip_id}/items", json={
        "day_number": 1, "name": "壽司大", "type": "restaurant",
        "time": "12:00", "location": "築地市場", "estimated_cost": 3000, "note": "要排隊",
    }, headers=_auth(token))
    await client.post(f"/api/trips/{trip_id}/items", json={
        "day_number": 2, "name": "迪士尼", "type": "attraction",
        "time": "09:00", "estimated_cost": 8000,
    }, headers=_auth(token))

    return trip_id, share_token, token, uid


# --- Task 5.1: Trip export ---

@pytest.mark.asyncio
async def test_export_trip_text(client):
    trip_id, _, token, _ = await _setup_trip_with_items(client)

    resp = await client.get(f"/api/trips/{trip_id}/export/text", headers=_auth(token))
    assert resp.status_code == 200
    text = resp.text
    assert "東京家族旅行" in text
    assert "東京" in text
    assert "淺草寺" in text
    assert "壽司大" in text
    assert "迪士尼" in text
    assert "Day 1" in text
    assert "Day 2" in text


@pytest.mark.asyncio
async def test_export_trip_json(client):
    trip_id, _, token, _ = await _setup_trip_with_items(client)

    resp = await client.get(f"/api/trips/{trip_id}/export/json", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "東京家族旅行"
    assert len(data["items"]) == 3
    assert data["destination"] == "東京"


@pytest.mark.asyncio
async def test_export_requires_auth(client):
    trip_id, _, token, _ = await _setup_trip_with_items(client)
    resp = await client.get(f"/api/trips/{trip_id}/export/text")
    assert resp.status_code == 401


# --- Task 5.2: Read-only share link ---

@pytest.mark.asyncio
async def test_share_link_no_auth_required(client):
    trip_id, share_token, _, _ = await _setup_trip_with_items(client)

    # No auth header — should still work
    resp = await client.get(f"/api/share/{share_token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "東京家族旅行"
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_share_link_invalid_token(client):
    resp = await client.get("/api/share/invalid-token-12345")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_share_link_includes_itinerary(client):
    _, share_token, _, _ = await _setup_trip_with_items(client)

    resp = await client.get(f"/api/share/{share_token}")
    data = resp.json()
    items = data["items"]
    names = [i["name"] for i in items]
    assert "淺草寺" in names
    assert "壽司大" in names
    assert "迪士尼" in names


# --- Task 5.3: Settlement export ---

@pytest.mark.asyncio
async def test_settlement_export_text(client):
    token1, uid1 = await _register(client, "+886500000010")
    token2, uid2 = await _register(client, "+886500000011")

    trip_resp = await client.post("/api/trips", json={
        "name": "Settlement Export Test", "destination": "Osaka",
        "start_date": "2026-07-01", "end_date": "2026-07-03",
    }, headers=_auth(token1))
    trip_id = trip_resp.json()["id"]
    share_token = trip_resp.json()["share_token"]
    await client.post(f"/api/trips/join/{share_token}", headers=_auth(token2))

    # Add expenses
    await client.post(f"/api/trips/{trip_id}/expenses", json={
        "amount": 2000, "payer_id": uid1,
    }, headers=_auth(token1))

    resp = await client.get(f"/api/trips/{trip_id}/settlement/export/text", headers=_auth(token1))
    assert resp.status_code == 200
    text = resp.text
    assert "旅遊拆帳結算" in text
    assert "2,000" in text
    assert "轉帳清單" in text


@pytest.mark.asyncio
async def test_settlement_export_balanced(client):
    """When balanced, should show '大家都結清了'."""
    token, uid = await _register(client, "+886500000020")

    trip_resp = await client.post("/api/trips", json={
        "name": "Balanced", "destination": "X",
        "start_date": "2026-07-01", "end_date": "2026-07-02",
    }, headers=_auth(token))
    trip_id = trip_resp.json()["id"]

    resp = await client.get(f"/api/trips/{trip_id}/settlement/export/text", headers=_auth(token))
    assert "結清" in resp.text
