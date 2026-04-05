"""Airline website ticket price crawler.

Spec: specs/travel-planner-app/spec.md — US-1
Task: 1.4 — Airline official website crawler

This module provides a pluggable crawler interface. Each airline gets its own
crawler implementation. For MVP, we provide a simulated crawler that returns
realistic pricing data, plus the base class for real implementations.
"""

import random
from abc import ABC, abstractmethod
from datetime import date

from app.tickets.models import FlightLeg


class AirlineCrawler(ABC):
    """Base class for airline-specific crawlers."""

    @abstractmethod
    async def fetch_price(
        self,
        origin: str,
        destination: str,
        travel_date: date,
        passengers: int = 1,
    ) -> FlightLeg | None:
        """Fetch price for a single flight leg.

        Returns None if no flight found on the route/date.
        """
        ...


class SimulatedCrawler(AirlineCrawler):
    """Simulated crawler for development and testing.

    Generates realistic-looking pricing based on route distance heuristics.
    Will be replaced by real airline crawlers in production.
    """

    # Base prices by rough route distance category (TWD per person)
    _BASE_PRICES = {
        "short": (2000, 6000),     # < 3h flights (e.g. TPE-HKG, TPE-NRT)
        "medium": (8000, 18000),   # 3-7h flights (e.g. TPE-BKK, TPE-SIN)
        "long": (15000, 35000),    # > 7h flights (e.g. TPE-LAX, TPE-LHR)
    }

    # Known short-haul routes
    _SHORT_ROUTES = {
        frozenset({"TPE", "HKG"}), frozenset({"TPE", "MFM"}),
        frozenset({"TPE", "NRT"}), frozenset({"TPE", "KIX"}),
        frozenset({"TPE", "ICN"}), frozenset({"TPE", "PVG"}),
        frozenset({"HKG", "NRT"}), frozenset({"HKG", "ICN"}),
        frozenset({"HKG", "BKK"}), frozenset({"HKG", "SIN"}),
        frozenset({"ICN", "NRT"}), frozenset({"ICN", "KIX"}),
        frozenset({"MNL", "HKG"}), frozenset({"MNL", "TPE"}),
    }

    _MEDIUM_ROUTES = {
        frozenset({"TPE", "BKK"}), frozenset({"TPE", "SIN"}),
        frozenset({"TPE", "KUL"}), frozenset({"TPE", "SGN"}),
        frozenset({"TPE", "HAN"}), frozenset({"TPE", "MNL"}),
        frozenset({"HKG", "KUL"}), frozenset({"NRT", "BKK"}),
        frozenset({"NRT", "SIN"}), frozenset({"ICN", "BKK"}),
    }

    _AIRLINES = ["華航 CI", "長榮 BR", "國泰 CX", "星宇 JX", "虎航 IT", "酷航 TR"]

    def _get_distance_category(self, origin: str, destination: str) -> str:
        route = frozenset({origin, destination})
        if route in self._SHORT_ROUTES:
            return "short"
        if route in self._MEDIUM_ROUTES:
            return "medium"
        return "long"

    async def fetch_price(
        self,
        origin: str,
        destination: str,
        travel_date: date,
        passengers: int = 1,
    ) -> FlightLeg | None:
        category = self._get_distance_category(origin, destination)
        low, high = self._BASE_PRICES[category]

        # Add some date-based variation (weekends cost more)
        multiplier = 1.0
        if travel_date.weekday() >= 5:  # Saturday or Sunday
            multiplier = 1.2

        price = round(random.uniform(low, high) * multiplier)
        airline = random.choice(self._AIRLINES)
        flight_num = f"{airline.split()[1]}{random.randint(100, 999)}"

        return FlightLeg(
            origin=origin,
            destination=destination,
            airline=airline,
            flight_number=flight_num,
            departure_time=f"{random.randint(6, 22):02d}:{random.choice(['00', '15', '30', '45'])}",
            arrival_time=f"{random.randint(8, 23):02d}:{random.choice(['00', '15', '30', '45'])}",
            price=price,
        )


# Registry of available crawlers
_crawler_instance: AirlineCrawler | None = None


def get_crawler() -> AirlineCrawler:
    """Get the active crawler instance."""
    global _crawler_instance
    if _crawler_instance is None:
        _crawler_instance = SimulatedCrawler()
    return _crawler_instance


def set_crawler(crawler: AirlineCrawler) -> None:
    """Replace the crawler (for testing or switching to real crawlers)."""
    global _crawler_instance
    _crawler_instance = crawler
