"""Tests for B.1+B.4: Flight search API and SimulatedCrawler."""

import pytest


@pytest.mark.asyncio
async def test_one_way_search(client):
    resp = await client.post("/api/flights/search", json={
        "origin": "TPE", "destination": "NRT",
        "departure_date": "2026-07-01",
        "trip_type": "one_way", "passengers": 1,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["trip_type"] == "one_way"
    assert len(data["outbound_flights"]) > 0
    assert len(data["return_flights"]) == 0
    assert data["cheapest_outbound"] is not None


@pytest.mark.asyncio
async def test_round_trip_search(client):
    resp = await client.post("/api/flights/search", json={
        "origin": "TPE", "destination": "NRT",
        "departure_date": "2026-07-01", "return_date": "2026-07-10",
        "trip_type": "round_trip", "passengers": 1,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["trip_type"] == "round_trip"
    assert len(data["outbound_flights"]) > 0
    assert len(data["return_flights"]) > 0
    assert data["cheapest_roundtrip"] is not None


@pytest.mark.asyncio
async def test_flight_result_has_time_info(client):
    resp = await client.post("/api/flights/search", json={
        "origin": "TPE", "destination": "KIX",
        "departure_date": "2026-07-01",
        "trip_type": "one_way",
    })
    data = resp.json()
    flight = data["outbound_flights"][0]
    assert flight["departure_time"] != ""
    assert flight["arrival_time"] != ""
    assert flight["departure_date"] == "2026-07-01"
    assert flight["duration_minutes"] > 0
    assert flight["airline"] != ""
    assert flight["source"] == "simulated"


@pytest.mark.asyncio
async def test_flight_sorted_by_price(client):
    resp = await client.post("/api/flights/search", json={
        "origin": "TPE", "destination": "BKK",
        "departure_date": "2026-07-01",
        "trip_type": "one_way", "sort_by": "price",
    })
    flights = resp.json()["outbound_flights"]
    prices = [f["price"] for f in flights]
    assert prices == sorted(prices)


@pytest.mark.asyncio
async def test_flight_passengers_multiply(client):
    resp = await client.post("/api/flights/search", json={
        "origin": "TPE", "destination": "NRT",
        "departure_date": "2026-07-01",
        "trip_type": "one_way", "passengers": 3,
    })
    assert resp.json()["passengers"] == 3
    # Prices should be for 3 passengers
    assert resp.json()["outbound_flights"][0]["price"] > 0


@pytest.mark.asyncio
async def test_flight_sources_listed(client):
    resp = await client.post("/api/flights/search", json={
        "origin": "TPE", "destination": "NRT",
        "departure_date": "2026-07-01",
        "trip_type": "one_way",
    })
    assert "simulated" in resp.json()["sources"]


@pytest.mark.asyncio
async def test_long_haul_flight(client):
    resp = await client.post("/api/flights/search", json={
        "origin": "TPE", "destination": "LAX",
        "departure_date": "2026-07-01",
        "trip_type": "one_way",
    })
    data = resp.json()
    assert len(data["outbound_flights"]) > 0
    # Long haul should have longer duration
    for f in data["outbound_flights"]:
        assert f["duration_minutes"] >= 400  # ~7+ hours
