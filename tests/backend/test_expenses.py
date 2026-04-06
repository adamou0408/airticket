"""Tests for expenses — database-backed."""

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


async def _setup_trip_with_2(client):
    token1, uid1 = await _register(client, "+886600000001")
    token2, uid2 = await _register(client, "+886600000002")
    trip = await client.post("/api/trips", json={
        "name": "Expense Test", "destination": "Tokyo",
        "start_date": "2026-07-01", "end_date": "2026-07-05", "budget": 100000,
    }, headers=_auth(token1))
    trip_id = trip.json()["id"]
    await client.post(f"/api/trips/join/{trip.json()['share_token']}", headers=_auth(token2))
    return trip_id, token1, uid1, token2, uid2


@pytest.mark.asyncio
async def test_add_expense_quick(client):
    trip_id, token1, uid1, _, _ = await _setup_trip_with_2(client)
    resp = await client.post(f"/api/trips/{trip_id}/expenses", json={"amount": 3000, "payer_id": uid1}, headers=_auth(token1))
    assert resp.status_code == 201
    assert resp.json()["amount"] == 3000


@pytest.mark.asyncio
async def test_list_expenses(client):
    trip_id, token1, uid1, token2, uid2 = await _setup_trip_with_2(client)
    await client.post(f"/api/trips/{trip_id}/expenses", json={"amount": 1000, "payer_id": uid1}, headers=_auth(token1))
    await client.post(f"/api/trips/{trip_id}/expenses", json={"amount": 2000, "payer_id": uid2}, headers=_auth(token2))
    resp = await client.get(f"/api/trips/{trip_id}/expenses", headers=_auth(token1))
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_budget_summary(client):
    trip_id, token1, uid1, _, _ = await _setup_trip_with_2(client)
    await client.post(f"/api/trips/{trip_id}/items", json={"day_number": 1, "name": "Hotel", "type": "accommodation", "estimated_cost": 30000}, headers=_auth(token1))
    await client.post(f"/api/trips/{trip_id}/expenses", json={"amount": 5000, "payer_id": uid1, "category": "food"}, headers=_auth(token1))
    resp = await client.get(f"/api/trips/{trip_id}/expenses/budget", headers=_auth(token1))
    data = resp.json()
    assert data["budget"] == 100000
    assert data["estimated_total"] == 30000
    assert data["actual_total"] == 5000


@pytest.mark.asyncio
async def test_settlement_simple(client):
    trip_id, token1, uid1, _, uid2 = await _setup_trip_with_2(client)
    await client.post(f"/api/trips/{trip_id}/expenses", json={"amount": 1000, "payer_id": uid1}, headers=_auth(token1))
    resp = await client.get(f"/api/trips/{trip_id}/expenses/settlement", headers=_auth(token1))
    entries = resp.json()["entries"]
    assert len(entries) == 1
    assert entries[0]["from_user"] == uid2
    assert entries[0]["to_user"] == uid1
    assert entries[0]["amount"] == 500


@pytest.mark.asyncio
async def test_settlement_balanced(client):
    trip_id, token1, uid1, token2, uid2 = await _setup_trip_with_2(client)
    await client.post(f"/api/trips/{trip_id}/expenses", json={"amount": 1000, "payer_id": uid1}, headers=_auth(token1))
    await client.post(f"/api/trips/{trip_id}/expenses", json={"amount": 1000, "payer_id": uid2}, headers=_auth(token2))
    resp = await client.get(f"/api/trips/{trip_id}/expenses/settlement", headers=_auth(token1))
    assert len(resp.json()["entries"]) == 0


@pytest.mark.asyncio
async def test_mark_settled(client):
    trip_id, token1, uid1, _, uid2 = await _setup_trip_with_2(client)
    await client.post(f"/api/trips/{trip_id}/expenses", json={"amount": 1000, "payer_id": uid1}, headers=_auth(token1))
    await client.put(f"/api/trips/{trip_id}/expenses/settlement/settle?from_user={uid2}&to_user={uid1}", headers=_auth(token1))
    resp = await client.get(f"/api/trips/{trip_id}/expenses/settlement", headers=_auth(token1))
    assert resp.json()["entries"][0]["settled"] is True
