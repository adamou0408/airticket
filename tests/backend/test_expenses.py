"""Tests for Phase 4: Expense recording, budget estimation, settlement.

Task 4.1-4.2: Data models + quick expense recording
Task 4.3: Budget estimation
Task 4.4: Split/settlement engine (minimum transfers)
"""

import pytest
import pytest_asyncio


async def _register(client, phone: str) -> tuple[str, int]:
    """Register and return (token, user_id)."""
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


async def _setup_trip_with_2_members(client):
    """Helper: create trip with 2 members, return tokens and IDs."""
    token1, uid1 = await _register(client, "+886600000001")
    token2, uid2 = await _register(client, "+886600000002")

    trip_resp = await client.post("/api/trips", json={
        "name": "Expense Test Trip", "destination": "Tokyo",
        "start_date": "2026-07-01", "end_date": "2026-07-05",
        "budget": 100000,
    }, headers=_auth(token1))
    trip_id = trip_resp.json()["id"]
    share_token = trip_resp.json()["share_token"]

    await client.post(f"/api/trips/join/{share_token}", headers=_auth(token2))

    return trip_id, token1, uid1, token2, uid2


# --- Task 4.2: Quick expense recording ---

@pytest.mark.asyncio
async def test_add_expense_quick(client):
    trip_id, token1, uid1, _, _ = await _setup_trip_with_2_members(client)

    resp = await client.post(f"/api/trips/{trip_id}/expenses", json={
        "amount": 3000,
        "payer_id": uid1,
    }, headers=_auth(token1))
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 3000
    assert data["payer_id"] == uid1
    assert data["category"] == "other"  # default
    assert data["split_method"] == "equal"  # default


@pytest.mark.asyncio
async def test_add_expense_with_details(client):
    trip_id, token1, uid1, _, _ = await _setup_trip_with_2_members(client)

    resp = await client.post(f"/api/trips/{trip_id}/expenses", json={
        "amount": 5000,
        "payer_id": uid1,
        "category": "food",
        "note": "壽司大餐",
        "currency": "JPY",
    }, headers=_auth(token1))
    assert resp.status_code == 201
    assert resp.json()["category"] == "food"
    assert resp.json()["note"] == "壽司大餐"
    assert resp.json()["currency"] == "JPY"


@pytest.mark.asyncio
async def test_list_expenses(client):
    trip_id, token1, uid1, token2, uid2 = await _setup_trip_with_2_members(client)

    await client.post(f"/api/trips/{trip_id}/expenses", json={
        "amount": 1000, "payer_id": uid1,
    }, headers=_auth(token1))
    await client.post(f"/api/trips/{trip_id}/expenses", json={
        "amount": 2000, "payer_id": uid2,
    }, headers=_auth(token2))

    resp = await client.get(f"/api/trips/{trip_id}/expenses", headers=_auth(token1))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# --- Task 4.3: Budget estimation ---

@pytest.mark.asyncio
async def test_budget_summary(client):
    trip_id, token1, uid1, _, uid2 = await _setup_trip_with_2_members(client)

    # Add itinerary item with estimated cost
    await client.post(f"/api/trips/{trip_id}/items", json={
        "day_number": 1, "name": "Hotel", "type": "accommodation",
        "estimated_cost": 30000,
    }, headers=_auth(token1))

    # Add actual expense
    await client.post(f"/api/trips/{trip_id}/expenses", json={
        "amount": 5000, "payer_id": uid1, "category": "food",
    }, headers=_auth(token1))

    resp = await client.get(f"/api/trips/{trip_id}/expenses/budget", headers=_auth(token1))
    assert resp.status_code == 200
    data = resp.json()
    assert data["budget"] == 100000
    assert data["estimated_total"] == 30000
    assert data["actual_total"] == 5000
    assert data["by_category"]["food"] == 5000


@pytest.mark.asyncio
async def test_budget_over_budget_detection(client):
    trip_id, token1, uid1, _, _ = await _setup_trip_with_2_members(client)

    # Spend more than budget (100000)
    for _ in range(11):
        await client.post(f"/api/trips/{trip_id}/expenses", json={
            "amount": 10000, "payer_id": uid1,
        }, headers=_auth(token1))

    resp = await client.get(f"/api/trips/{trip_id}/expenses/budget", headers=_auth(token1))
    data = resp.json()
    assert data["actual_total"] == 110000
    assert data["over_budget"] is True


# --- Task 4.4: Settlement engine ---

@pytest.mark.asyncio
async def test_settlement_simple_equal_split(client):
    """User1 pays 1000, split equally between 2 people → User2 owes User1 500."""
    trip_id, token1, uid1, _, uid2 = await _setup_trip_with_2_members(client)

    await client.post(f"/api/trips/{trip_id}/expenses", json={
        "amount": 1000, "payer_id": uid1,
    }, headers=_auth(token1))

    resp = await client.get(f"/api/trips/{trip_id}/expenses/settlement", headers=_auth(token1))
    assert resp.status_code == 200
    data = resp.json()
    entries = data["entries"]
    assert len(entries) == 1
    assert entries[0]["from_user"] == uid2
    assert entries[0]["to_user"] == uid1
    assert entries[0]["amount"] == 500


@pytest.mark.asyncio
async def test_settlement_multiple_expenses(client):
    """User1 pays 1000, User2 pays 600 → net: User2 owes User1 200."""
    trip_id, token1, uid1, token2, uid2 = await _setup_trip_with_2_members(client)

    await client.post(f"/api/trips/{trip_id}/expenses", json={
        "amount": 1000, "payer_id": uid1,
    }, headers=_auth(token1))
    await client.post(f"/api/trips/{trip_id}/expenses", json={
        "amount": 600, "payer_id": uid2,
    }, headers=_auth(token2))

    resp = await client.get(f"/api/trips/{trip_id}/expenses/settlement", headers=_auth(token1))
    entries = resp.json()["entries"]
    assert len(entries) == 1
    # User1 paid 1000, share=800. User2 paid 600, share=800. Net: User2 owes User1 200
    assert entries[0]["from_user"] == uid2
    assert entries[0]["to_user"] == uid1
    assert entries[0]["amount"] == 200


@pytest.mark.asyncio
async def test_settlement_balanced_no_transfers(client):
    """Both pay equal amounts → no transfers needed."""
    trip_id, token1, uid1, token2, uid2 = await _setup_trip_with_2_members(client)

    await client.post(f"/api/trips/{trip_id}/expenses", json={
        "amount": 1000, "payer_id": uid1,
    }, headers=_auth(token1))
    await client.post(f"/api/trips/{trip_id}/expenses", json={
        "amount": 1000, "payer_id": uid2,
    }, headers=_auth(token2))

    resp = await client.get(f"/api/trips/{trip_id}/expenses/settlement", headers=_auth(token1))
    assert len(resp.json()["entries"]) == 0


@pytest.mark.asyncio
async def test_mark_settled(client):
    trip_id, token1, uid1, _, uid2 = await _setup_trip_with_2_members(client)

    await client.post(f"/api/trips/{trip_id}/expenses", json={
        "amount": 1000, "payer_id": uid1,
    }, headers=_auth(token1))

    # Mark as settled
    resp = await client.put(
        f"/api/trips/{trip_id}/expenses/settlement/settle?from_user={uid2}&to_user={uid1}",
        headers=_auth(token1),
    )
    assert resp.status_code == 200

    # Check settlement shows settled=True
    settle_resp = await client.get(f"/api/trips/{trip_id}/expenses/settlement", headers=_auth(token1))
    entries = settle_resp.json()["entries"]
    assert entries[0]["settled"] is True


# --- Settlement algorithm: 3+ people ---

@pytest.mark.asyncio
async def test_settlement_three_people_minimum_transfers(client):
    """3 people: A pays 900, split equal (300 each).
    B owes A 300, C owes A 300.
    Minimum transfers = 2.
    """
    token1, uid1 = await _register(client, "+886600000010")
    token2, uid2 = await _register(client, "+886600000011")
    token3, uid3 = await _register(client, "+886600000012")

    trip_resp = await client.post("/api/trips", json={
        "name": "3 People", "destination": "Osaka",
        "start_date": "2026-07-01", "end_date": "2026-07-03",
    }, headers=_auth(token1))
    trip_id = trip_resp.json()["id"]
    share_token = trip_resp.json()["share_token"]

    await client.post(f"/api/trips/join/{share_token}", headers=_auth(token2))
    await client.post(f"/api/trips/join/{share_token}", headers=_auth(token3))

    # A pays 900 for everyone
    await client.post(f"/api/trips/{trip_id}/expenses", json={
        "amount": 900, "payer_id": uid1,
    }, headers=_auth(token1))

    resp = await client.get(f"/api/trips/{trip_id}/expenses/settlement", headers=_auth(token1))
    entries = resp.json()["entries"]

    # Should be exactly 2 transfers
    assert len(entries) == 2
    total_to_a = sum(e["amount"] for e in entries if e["to_user"] == uid1)
    assert total_to_a == 600  # B owes 300 + C owes 300
