"""Tests for flight search API — after mock removal (US-17).

Without SimulatedCrawler, flight search returns empty results
in test environment. Tests verify API structure is correct.
"""

import pytest


@pytest.mark.asyncio
async def test_one_way_search_returns_200(client):
    resp = await client.post("/api/flights/search", json={
        "origin": "TPE", "destination": "NRT",
        "departure_date": "2026-07-01",
        "trip_type": "one_way", "passengers": 1,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["trip_type"] == "one_way"
    assert isinstance(data["outbound_flights"], list)
    assert data["return_flights"] == []


@pytest.mark.asyncio
async def test_round_trip_search_returns_200(client):
    resp = await client.post("/api/flights/search", json={
        "origin": "TPE", "destination": "NRT",
        "departure_date": "2026-07-01", "return_date": "2026-07-10",
        "trip_type": "round_trip", "passengers": 1,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["trip_type"] == "round_trip"
    assert isinstance(data["outbound_flights"], list)
    assert isinstance(data["return_flights"], list)


@pytest.mark.asyncio
async def test_no_simulated_source_in_results(client):
    """No simulated flights should appear (US-17)."""
    resp = await client.post("/api/flights/search", json={
        "origin": "TPE", "destination": "KIX",
        "departure_date": "2026-07-01", "trip_type": "one_way",
    })
    data = resp.json()
    for f in data["outbound_flights"]:
        assert f["source"] != "simulated"
    assert "simulated" not in data.get("sources", [])


@pytest.mark.asyncio
async def test_flight_search_validation(client):
    """Missing required fields should return 422."""
    resp = await client.post("/api/flights/search", json={
        "origin": "TPE",
    })
    assert resp.status_code == 422
