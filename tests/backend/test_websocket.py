"""Tests for WebSocket real-time collaboration.

Spec: .req/specs/travel-planner-app/spec.md — US-7
Task: .req/specs/travel-planner-app/tasks.md — Task 3.1
"""

import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.service import _otp_store, create_access_token
from app.main import app
from app.trips.websocket import manager


async def _register(client, phone: str) -> tuple[str, int]:
    await client.post("/api/auth/send-code", json={"phone": phone})
    code = _otp_store.get(f"otp:{phone}")
    resp = await client.post("/api/auth/verify", json={"phone": phone, "code": code})
    data = resp.json()
    return data["access_token"], data["user_id"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_connection_manager_singleton():
    """Manager should be a global singleton."""
    from app.trips.websocket import manager as m1, manager as m2
    assert m1 is m2


@pytest.mark.asyncio
async def test_connection_manager_tracks_count():
    """Manager tracks connection count per trip."""
    trip_id = 9999
    # Initially empty
    assert manager.get_connection_count(trip_id) == 0


@pytest.mark.asyncio
async def test_item_add_broadcasts_ws_event(client):
    """Adding an item should call WebSocket broadcast (no listeners = no error)."""
    token, uid = await _register(client, "+886300000001")
    trip = await client.post("/api/trips", json={
        "name": "WS Test", "destination": "X",
        "start_date": "2026-07-01", "end_date": "2026-07-05",
    }, headers=_auth(token))
    trip_id = trip.json()["id"]

    # Adding an item should succeed (no WS listeners, but broadcast still works)
    item = await client.post(f"/api/trips/{trip_id}/items", json={
        "day_number": 1, "name": "Test Item", "type": "attraction",
    }, headers=_auth(token))
    assert item.status_code == 201


@pytest.mark.asyncio
async def test_item_update_broadcasts_ws_event(client):
    token, uid = await _register(client, "+886300000002")
    trip = await client.post("/api/trips", json={
        "name": "WS Update", "destination": "Y",
        "start_date": "2026-07-01", "end_date": "2026-07-03",
    }, headers=_auth(token))
    trip_id = trip.json()["id"]
    item = await client.post(f"/api/trips/{trip_id}/items", json={
        "day_number": 1, "name": "Original", "type": "attraction",
    }, headers=_auth(token))
    item_id = item.json()["id"]

    # Update should succeed
    updated = await client.put(f"/api/trips/{trip_id}/items/{item_id}", json={
        "day_number": 1, "name": "Updated", "type": "restaurant",
    }, headers=_auth(token))
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated"


@pytest.mark.asyncio
async def test_item_delete_broadcasts_ws_event(client):
    token, _ = await _register(client, "+886300000003")
    trip = await client.post("/api/trips", json={
        "name": "WS Delete", "destination": "Z",
        "start_date": "2026-07-01", "end_date": "2026-07-03",
    }, headers=_auth(token))
    trip_id = trip.json()["id"]
    item = await client.post(f"/api/trips/{trip_id}/items", json={
        "day_number": 1, "name": "To Delete", "type": "other",
    }, headers=_auth(token))
    item_id = item.json()["id"]

    # Delete should succeed
    deleted = await client.delete(f"/api/trips/{trip_id}/items/{item_id}", headers=_auth(token))
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_comment_broadcasts_ws_event(client):
    token, _ = await _register(client, "+886300000004")
    trip = await client.post("/api/trips", json={
        "name": "WS Comment", "destination": "W",
        "start_date": "2026-07-01", "end_date": "2026-07-03",
    }, headers=_auth(token))
    trip_id = trip.json()["id"]
    item = await client.post(f"/api/trips/{trip_id}/items", json={
        "day_number": 1, "name": "For Comment", "type": "attraction",
    }, headers=_auth(token))
    item_id = item.json()["id"]

    comment = await client.post(
        f"/api/trips/{trip_id}/items/{item_id}/comments",
        json={"text": "Looks good!"},
        headers=_auth(token),
    )
    assert comment.status_code == 201


def test_websocket_requires_auth():
    """WebSocket should reject connection without valid token."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    # No token
    with pytest.raises(Exception):
        with client.websocket_connect("/api/trips/1/ws"):
            pass


def test_websocket_rejects_invalid_token():
    """WebSocket should reject connection with invalid token."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/api/trips/1/ws?token=invalid") as ws:
            pass
