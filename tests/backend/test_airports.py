"""Tests for A.1 + A.2: Airport data and search API."""

import pytest
from app.airports.service import search_airports, get_airport, get_airport_count


def test_airport_data_loaded():
    count = get_airport_count()
    assert count >= 5000, f"Expected 5000+ airports, got {count}"


def test_search_by_iata_exact():
    results = search_airports("TPE")
    assert len(results) >= 1
    assert results[0]["iata"] == "TPE"


def test_search_by_city_english():
    results = search_airports("Tokyo")
    codes = [a["iata"] for a in results]
    assert "NRT" in codes or "HND" in codes


def test_search_by_city_chinese():
    results = search_airports("東京")
    codes = [a["iata"] for a in results]
    assert "NRT" in codes or "HND" in codes


def test_search_by_country_chinese():
    results = search_airports("日本")
    assert len(results) > 0
    # All results should be in Japan
    for a in results:
        assert a.get("country_zh") == "日本" or "Japan" in a.get("country", "")


def test_search_fuzzy_partial():
    results = search_airports("osa")  # should match Osaka
    codes = [a["iata"] for a in results]
    assert "KIX" in codes or "ITM" in codes


def test_search_empty_returns_popular():
    results = search_airports("")
    assert len(results) > 0
    assert all(a.get("popular") for a in results)


def test_get_airport_by_code():
    airport = get_airport("NRT")
    assert airport is not None
    assert airport["iata"] == "NRT"
    assert airport["city_zh"] == "東京"


def test_get_airport_not_found():
    assert get_airport("ZZZ") is None


@pytest.mark.asyncio
async def test_airport_search_api(client):
    resp = await client.get("/api/airports?q=taipei")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] > 0
    codes = [a["iata"] for a in data["results"]]
    assert "TPE" in codes


@pytest.mark.asyncio
async def test_airport_search_api_chinese(client):
    resp = await client.get("/api/airports?q=曼谷")
    assert resp.status_code == 200
    codes = [a["iata"] for a in resp.json()["results"]]
    assert "BKK" in codes


@pytest.mark.asyncio
async def test_airport_count_api(client):
    resp = await client.get("/api/airports/count")
    assert resp.status_code == 200
    assert resp.json()["count"] >= 5000


@pytest.mark.asyncio
async def test_airport_get_by_code_api(client):
    resp = await client.get("/api/airports/HKG")
    assert resp.status_code == 200
    assert resp.json()["iata"] == "HKG"
    assert resp.json()["city_zh"] == "香港"
