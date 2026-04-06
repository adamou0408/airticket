"""Tests for B.2 + B.3: EVA Air and Starlux crawlers.

These tests verify the crawler structure and parsing logic
without requiring a real browser (Playwright may not be available).
"""

import pytest
from datetime import date

from app.flights.evaair_crawler import EvaAirCrawler
from app.flights.starlux_crawler import StarluxCrawler
from app.flights.crawler_router import router, CrawlerRouter


def test_evaair_crawler_registered():
    """EVA Air crawler should be registered in the router."""
    names = [c.name for c in router.crawlers]
    assert "evaair" in names


def test_starlux_crawler_registered():
    """Starlux crawler should be registered in the router."""
    names = [c.name for c in router.crawlers]
    assert "starlux" in names


def test_evaair_parse_flight_card():
    """Test EVA Air DOM text parsing."""
    crawler = EvaAirCrawler()
    text = "BR108\n08:30\n12:45\n經濟艙\nTWD 8,500"
    result = crawler._parse_flight_card(text, "TPE", "NRT", date(2026, 7, 1), 1)
    assert result is not None
    assert result.airline == "長榮航空"
    assert result.flight_number == "BR108"
    assert result.departure_time == "08:30"
    assert result.arrival_time == "12:45"
    assert result.price == 8500
    assert result.source == "evaair"


def test_starlux_parse_flight_card():
    """Test Starlux DOM text parsing."""
    crawler = StarluxCrawler()
    text = "JX800\n09:15\n13:30\nTWD 9,200"
    result = crawler._parse_flight_card(text, "TPE", "NRT", date(2026, 7, 1), 1)
    assert result is not None
    assert result.airline == "星宇航空"
    assert result.flight_number == "JX800"
    assert result.price == 9200
    assert result.source == "starlux"


def test_evaair_parse_with_passengers():
    """Price should multiply by passenger count."""
    crawler = EvaAirCrawler()
    text = "BR108\n08:30\n12:45\nTWD 8,500"
    result = crawler._parse_flight_card(text, "TPE", "NRT", date(2026, 7, 1), 3)
    assert result.price == 25500  # 8500 * 3


def test_evaair_parse_no_price():
    """Should return None if no price found."""
    crawler = EvaAirCrawler()
    result = crawler._parse_flight_card("No useful data here", "TPE", "NRT", date(2026, 7, 1), 1)
    assert result is None


def test_evaair_extract_prices_from_text():
    """Test fallback text extraction."""
    crawler = EvaAirCrawler()
    text = "BR108 08:30 12:45 TWD 8,500 BR110 14:00 18:30 TWD 12,000"
    results = crawler._extract_prices_from_text(text, "TPE", "NRT", date(2026, 7, 1), 1)
    assert len(results) >= 1
    assert all(r.source == "evaair" for r in results)


@pytest.mark.asyncio
async def test_evaair_graceful_fail():
    """Crawler should return empty list on failure, not crash."""
    crawler = EvaAirCrawler()
    results = await crawler.search("TPE", "NRT", date(2026, 7, 1), 1)
    # If Playwright not available, returns empty (graceful fail)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_starlux_graceful_fail():
    """Crawler should return empty list on failure, not crash."""
    crawler = StarluxCrawler()
    results = await crawler.search("TPE", "NRT", date(2026, 7, 1), 1)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_router_includes_simulated_and_real():
    """Router should always have simulated + registered real crawlers."""
    results, sources = await router.search("TPE", "NRT", date(2026, 7, 1), 1)
    assert "simulated" in sources
    assert len(results) > 0
