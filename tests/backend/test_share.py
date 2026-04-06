"""Tests for share/export — database-backed."""

import pytest

from app.auth.service import _otp_store


async def _register(client, phone: str) -> tuple[str, int]:
    await client.post("/api/auth/send-code", json={"phone": phone})
    code = _otp_store.get(f"otp:{phone}")
    resp = await client.post("/api/auth/verify", json={"phone": phone, "code": code})
    data = resp.json()
    return data["access_token"], data["user_id"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _setup_trip_with_items(client):
    token, uid = await _register(client, "+886500000001")
    trip = await client.post("/api/trips", json={
        "name": "東京家族旅行", "destination": "東京",
        "start_date": "2026-07-01", "end_date": "2026-07-03", "budget": 50000,
    }, headers=_auth(token))
    trip_id = trip.json()["id"]
    share_token = trip.json()["share_token"]
    await client.post(f"/api/trips/{trip_id}/items", json={"day_number": 1, "name": "淺草寺", "type": "attraction", "time": "10:00", "location": "東京淺草"}, headers=_auth(token))
    await client.post(f"/api/trips/{trip_id}/items", json={"day_number": 1, "name": "壽司大", "type": "restaurant", "time": "12:00", "estimated_cost": 3000}, headers=_auth(token))
    await client.post(f"/api/trips/{trip_id}/items", json={"day_number": 2, "name": "迪士尼", "type": "attraction", "time": "09:00", "estimated_cost": 8000}, headers=_auth(token))
    return trip_id, share_token, token, uid


@pytest.mark.asyncio
async def test_export_trip_text(client):
    trip_id, _, token, _ = await _setup_trip_with_items(client)
    resp = await client.get(f"/api/trips/{trip_id}/export/text", headers=_auth(token))
    assert resp.status_code == 200
    assert "東京家族旅行" in resp.text
    assert "淺草寺" in resp.text


@pytest.mark.asyncio
async def test_export_trip_json(client):
    trip_id, _, token, _ = await _setup_trip_with_items(client)
    resp = await client.get(f"/api/trips/{trip_id}/export/json", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["name"] == "東京家族旅行"
    assert len(resp.json()["items"]) == 3


@pytest.mark.asyncio
async def test_share_link_no_auth(client):
    _, share_token, _, _ = await _setup_trip_with_items(client)
    resp = await client.get(f"/api/share/{share_token}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "東京家族旅行"


@pytest.mark.asyncio
async def test_share_link_invalid(client):
    resp = await client.get("/api/share/invalid-token")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_settlement_export_text(client):
    token1, uid1 = await _register(client, "+886500000010")
    token2, uid2 = await _register(client, "+886500000011")
    trip = await client.post("/api/trips", json={"name": "Settle Test", "destination": "Osaka", "start_date": "2026-07-01", "end_date": "2026-07-03"}, headers=_auth(token1))
    trip_id = trip.json()["id"]
    await client.post(f"/api/trips/join/{trip.json()['share_token']}", headers=_auth(token2))
    await client.post(f"/api/trips/{trip_id}/expenses", json={"amount": 2000, "payer_id": uid1}, headers=_auth(token1))
    resp = await client.get(f"/api/trips/{trip_id}/settlement/export/text", headers=_auth(token1))
    assert resp.status_code == 200
    assert "拆帳結算" in resp.text
