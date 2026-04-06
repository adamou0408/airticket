"""Tests for ticket search — after mock removal (US-17).

With SimulatedCrawler removed, outstation search returns 0 results
in test environment (no real crawlers). Tests verify:
- API responds correctly with empty results
- No simulated source in responses
- Search structure is correct
"""

from datetime import date

import pytest

from app.tickets.models import SortBy, TicketSearchRequest
from app.tickets.service import search_outstation_tickets
from app.tickets.crawler import NullCrawler, get_crawler


def test_null_crawler_returns_none():
    """NullCrawler (default after mock removal) returns None."""
    import asyncio
    crawler = NullCrawler()
    result = asyncio.get_event_loop().run_until_complete(
        crawler.fetch_price("TPE", "NRT", date(2026, 7, 1))
    )
    assert result is None


@pytest.mark.asyncio
async def test_search_returns_empty_without_real_crawlers():
    """Without real crawlers, search returns 0 results (not simulated data)."""
    request = TicketSearchRequest(
        origin="TPE", destination="CDG",
        departure_date=date(2026, 7, 1), return_date=date(2026, 7, 10),
    )
    response = await search_outstation_tickets(request)
    assert response.result_count == 0
    assert response.origin == "TPE"
    assert response.destination == "CDG"


@pytest.mark.asyncio
async def test_search_api_returns_200_with_empty(client):
    """API should return 200 with empty results, not crash."""
    response = await client.post("/api/tickets/search", json={
        "origin": "TPE", "destination": "CDG",
        "departure_date": "2026-07-01", "return_date": "2026-07-10",
        "passengers": 1,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["result_count"] == 0
    assert data["results"] == []


@pytest.mark.asyncio
async def test_flights_search_no_simulated(client):
    """Flight search should not return simulated source."""
    response = await client.post("/api/flights/search", json={
        "origin": "TPE", "destination": "NRT",
        "departure_date": "2026-07-01", "trip_type": "one_way",
    })
    assert response.status_code == 200
    data = response.json()
    # No simulated flights
    for f in data.get("outbound_flights", []):
        assert f["source"] != "simulated"
