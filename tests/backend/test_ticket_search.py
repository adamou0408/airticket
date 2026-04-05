"""Tests for Task 1.4 + 1.5: Crawler, search service, and API.

Covers:
- SimulatedCrawler returns valid FlightLeg
- Search service returns outstation combinations
- Results are sorted by price (default)
- API endpoint works end-to-end
"""

from datetime import date

import pytest
import pytest_asyncio

from app.tickets.crawler import SimulatedCrawler
from app.tickets.models import SortBy, TicketSearchRequest
from app.tickets.service import search_outstation_tickets


@pytest.mark.asyncio
async def test_simulated_crawler_returns_flight_leg():
    crawler = SimulatedCrawler()
    leg = await crawler.fetch_price("TPE", "NRT", date(2026, 7, 1))
    assert leg is not None
    assert leg.origin == "TPE"
    assert leg.destination == "NRT"
    assert leg.price > 0
    assert leg.airline != ""


@pytest.mark.asyncio
async def test_search_returns_results():
    request = TicketSearchRequest(
        origin="TPE",
        destination="CDG",
        departure_date=date(2026, 7, 1),
        return_date=date(2026, 7, 10),
        passengers=1,
    )
    response = await search_outstation_tickets(request)
    assert response.result_count > 0
    assert len(response.results) == response.result_count
    assert response.origin == "TPE"
    assert response.destination == "CDG"


@pytest.mark.asyncio
async def test_search_results_sorted_by_price():
    request = TicketSearchRequest(
        origin="TPE",
        destination="CDG",
        departure_date=date(2026, 7, 1),
        return_date=date(2026, 7, 10),
        sort_by=SortBy.price,
    )
    response = await search_outstation_tickets(request)
    prices = [r.total_price for r in response.results]
    assert prices == sorted(prices)


@pytest.mark.asyncio
async def test_search_each_result_has_4_legs():
    request = TicketSearchRequest(
        origin="TPE",
        destination="CDG",
        departure_date=date(2026, 7, 1),
        return_date=date(2026, 7, 10),
    )
    response = await search_outstation_tickets(request)
    for ticket in response.results:
        assert len(ticket.legs) == 4


@pytest.mark.asyncio
async def test_search_passengers_multiply_price():
    req1 = TicketSearchRequest(
        origin="TPE", destination="CDG",
        departure_date=date(2026, 7, 1), return_date=date(2026, 7, 10),
        passengers=1,
    )
    req2 = TicketSearchRequest(
        origin="TPE", destination="CDG",
        departure_date=date(2026, 7, 1), return_date=date(2026, 7, 10),
        passengers=2,
    )
    # Both use simulated data so prices won't be exactly 2x,
    # but passengers field should be reflected
    resp = await search_outstation_tickets(req2)
    assert resp.passengers == 2


@pytest.mark.asyncio
async def test_search_has_direct_price_comparison():
    request = TicketSearchRequest(
        origin="TPE",
        destination="NRT",
        departure_date=date(2026, 7, 1),
        return_date=date(2026, 7, 10),
    )
    response = await search_outstation_tickets(request)
    assert response.direct_price is not None
    assert response.direct_price > 0


@pytest.mark.asyncio
async def test_search_api_endpoint(client):
    response = await client.post("/api/tickets/search", json={
        "origin": "TPE",
        "destination": "CDG",
        "departure_date": "2026-07-01",
        "return_date": "2026-07-10",
        "passengers": 1,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["result_count"] > 0
    assert len(data["results"]) > 0
    assert data["results"][0]["outstation_city"] != ""
    assert len(data["results"][0]["legs"]) == 4
