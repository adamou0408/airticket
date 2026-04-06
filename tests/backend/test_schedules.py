"""Tests for D.1 + D.2: Crawl schedule engine and API."""

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


@pytest.mark.asyncio
async def test_create_schedule(client):
    token, _ = await _register(client, "+886400000001")
    resp = await client.post("/api/crawl-schedules", json={
        "origin": "TPE", "destination": "NRT",
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["origin"] == "TPE"
    assert data["destination"] == "NRT"
    assert data["enabled"] is True


@pytest.mark.asyncio
async def test_list_schedules(client):
    token, _ = await _register(client, "+886400000002")
    await client.post("/api/crawl-schedules", json={"origin": "TPE", "destination": "NRT"}, headers=_auth(token))
    await client.post("/api/crawl-schedules", json={"origin": "TPE", "destination": "KIX"}, headers=_auth(token))

    resp = await client.get("/api/crawl-schedules", headers=_auth(token))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_dedup_schedule(client):
    token, _ = await _register(client, "+886400000003")
    await client.post("/api/crawl-schedules", json={"origin": "TPE", "destination": "NRT"}, headers=_auth(token))
    await client.post("/api/crawl-schedules", json={"origin": "TPE", "destination": "NRT"}, headers=_auth(token))

    resp = await client.get("/api/crawl-schedules", headers=_auth(token))
    assert len(resp.json()) == 1  # Deduped


@pytest.mark.asyncio
async def test_delete_schedule(client):
    token, _ = await _register(client, "+886400000004")
    create = await client.post("/api/crawl-schedules", json={"origin": "TPE", "destination": "BKK"}, headers=_auth(token))
    sid = create.json()["id"]

    resp = await client.delete(f"/api/crawl-schedules/{sid}", headers=_auth(token))
    assert resp.status_code == 204

    listing = await client.get("/api/crawl-schedules", headers=_auth(token))
    assert len(listing.json()) == 0


@pytest.mark.asyncio
async def test_toggle_schedule(client):
    token, _ = await _register(client, "+886400000005")
    create = await client.post("/api/crawl-schedules", json={"origin": "TPE", "destination": "SIN"}, headers=_auth(token))
    sid = create.json()["id"]
    assert create.json()["enabled"] is True

    # Toggle off
    resp = await client.put(f"/api/crawl-schedules/{sid}/toggle", headers=_auth(token))
    assert resp.json()["enabled"] is False

    # Toggle on
    resp = await client.put(f"/api/crawl-schedules/{sid}/toggle", headers=_auth(token))
    assert resp.json()["enabled"] is True


@pytest.mark.asyncio
async def test_default_routes(client):
    resp = await client.get("/api/crawl-schedules/default-routes")
    assert resp.status_code == 200
    routes = resp.json()
    assert len(routes) > 0
    # TPE→NRT should be in defaults
    assert any(r["origin"] == "TPE" and r["destination"] == "NRT" for r in routes)


@pytest.mark.asyncio
async def test_manual_crawl(client):
    token, _ = await _register(client, "+886400000006")
    resp = await client.post("/api/crawl-schedules/crawl-now", json={
        "origin": "TPE", "destination": "NRT",
    }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["origin"] == "TPE"
    assert data["destination"] == "NRT"
    assert isinstance(data["total_flights"], int)  # May be 0 without real crawlers
    assert "simulated" not in data.get("sources", [])  # US-17: no mock


@pytest.mark.asyncio
async def test_requires_auth(client):
    resp = await client.get("/api/crawl-schedules")
    assert resp.status_code == 401
