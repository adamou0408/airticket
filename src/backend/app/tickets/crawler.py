"""Airline website ticket price crawler.

Spec: specs/travel-planner-app/spec.md — US-1
Task: 1.4 — Airline official website crawler
Iterate: 2026-04-05 — Added full datetime and flight duration
"""

import random
from abc import ABC, abstractmethod
from datetime import date, timedelta

from app.tickets.models import FlightLeg


# Flight duration estimates (minutes) by route distance
DURATION = {
    "short": (90, 180),    # 1.5-3h
    "medium": (210, 360),  # 3.5-6h
    "long": (480, 840),    # 8-14h
}


class AirlineCrawler(ABC):
    @abstractmethod
    async def fetch_price(
        self, origin: str, destination: str, travel_date: date, passengers: int = 1,
    ) -> FlightLeg | None:
        ...


class SimulatedCrawler(AirlineCrawler):
    """Simulated crawler with realistic time data."""

    _BASE_PRICES = {
        "short": (2000, 6000),
        "medium": (8000, 18000),
        "long": (15000, 35000),
    }

    _SHORT_ROUTES = {
        frozenset({"TPE", "HKG"}), frozenset({"TPE", "MFM"}),
        frozenset({"TPE", "NRT"}), frozenset({"TPE", "KIX"}),
        frozenset({"TPE", "ICN"}), frozenset({"TPE", "PVG"}),
        frozenset({"HKG", "NRT"}), frozenset({"HKG", "ICN"}),
        frozenset({"HKG", "BKK"}), frozenset({"HKG", "SIN"}),
        frozenset({"ICN", "NRT"}), frozenset({"ICN", "KIX"}),
        frozenset({"MNL", "HKG"}), frozenset({"MNL", "TPE"}),
        frozenset({"MFM", "TPE"}), frozenset({"KUL", "SIN"}),
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
        self, origin: str, destination: str, travel_date: date, passengers: int = 1,
    ) -> FlightLeg | None:
        category = self._get_distance_category(origin, destination)
        low, high = self._BASE_PRICES[category]

        multiplier = 1.2 if travel_date.weekday() >= 5 else 1.0
        price = round(random.uniform(low, high) * multiplier)

        airline = random.choice(self._AIRLINES)
        flight_num = f"{airline.split()[1]}{random.randint(100, 999)}"

        # Generate realistic departure time and flight duration
        dep_hour = random.randint(6, 22)
        dep_min = random.choice([0, 15, 30, 45])
        dur_low, dur_high = DURATION[category]
        duration = random.randint(dur_low, dur_high)

        # Calculate arrival
        arr_total_min = dep_hour * 60 + dep_min + duration
        arr_hour = (arr_total_min // 60) % 24
        arr_min = arr_total_min % 60
        next_day = arr_total_min >= 24 * 60

        arr_date = travel_date + timedelta(days=1) if next_day else travel_date

        return FlightLeg(
            origin=origin,
            destination=destination,
            airline=airline,
            flight_number=flight_num,
            departure_time=f"{dep_hour:02d}:{dep_min:02d}",
            arrival_time=f"{arr_hour:02d}:{arr_min:02d}",
            departure_date=travel_date.isoformat(),
            arrival_date=arr_date.isoformat(),
            flight_duration_minutes=duration,
            price=price,
            next_day=next_day,
        )


_crawler_instance: AirlineCrawler | None = None


def get_crawler() -> AirlineCrawler:
    global _crawler_instance
    if _crawler_instance is None:
        _crawler_instance = SimulatedCrawler()
    return _crawler_instance


def set_crawler(crawler: AirlineCrawler) -> None:
    global _crawler_instance
    _crawler_instance = crawler
