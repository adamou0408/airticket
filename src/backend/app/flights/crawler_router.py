"""CrawlerRouter — dispatches to multiple airline crawlers in parallel.

US-15: Real airline pricing data
"""

import asyncio
import random
from abc import ABC, abstractmethod
from datetime import date

from app.flights.models import FlightResult

# Flight duration estimates by distance
DURATION_RANGES = {
    "short": (90, 180),
    "medium": (210, 360),
    "long": (480, 840),
}

SHORT_ROUTES = {
    frozenset({"TPE", "HKG"}), frozenset({"TPE", "MFM"}),
    frozenset({"TPE", "NRT"}), frozenset({"TPE", "KIX"}),
    frozenset({"TPE", "ICN"}), frozenset({"TPE", "PVG"}),
    frozenset({"TPE", "HND"}), frozenset({"TPE", "FUK"}),
    frozenset({"TPE", "OKA"}), frozenset({"TPE", "CTS"}),
    frozenset({"TPE", "NGO"}), frozenset({"TPE", "GMP"}),
    frozenset({"HKG", "NRT"}), frozenset({"HKG", "ICN"}),
    frozenset({"ICN", "NRT"}), frozenset({"ICN", "KIX"}),
    frozenset({"MFM", "TPE"}), frozenset({"TPE", "MNL"}),
}

MEDIUM_ROUTES = {
    frozenset({"TPE", "BKK"}), frozenset({"TPE", "SIN"}),
    frozenset({"TPE", "KUL"}), frozenset({"TPE", "SGN"}),
    frozenset({"TPE", "HAN"}), frozenset({"TPE", "DPS"}),
    frozenset({"TPE", "CGK"}), frozenset({"HKG", "BKK"}),
    frozenset({"NRT", "BKK"}), frozenset({"NRT", "SIN"}),
}


def _get_distance(origin: str, dest: str) -> str:
    route = frozenset({origin, dest})
    if route in SHORT_ROUTES:
        return "short"
    if route in MEDIUM_ROUTES:
        return "medium"
    return "long"


class FlightCrawler(ABC):
    """Base class for airline flight crawlers."""

    name: str = "base"

    @abstractmethod
    async def search(
        self, origin: str, destination: str, travel_date: date, passengers: int = 1,
    ) -> list[FlightResult]:
        ...


class SimulatedFlightCrawler(FlightCrawler):
    """Generates realistic simulated flights for any route."""

    name = "simulated"

    AIRLINES = [
        ("長榮航空", "BR"), ("星宇航空", "JX"), ("華航", "CI"),
        ("國泰航空", "CX"), ("日本航空", "JL"), ("全日空", "NH"),
        ("大韓航空", "KE"), ("新加坡航空", "SQ"), ("泰國航空", "TG"),
    ]

    async def search(
        self, origin: str, destination: str, travel_date: date, passengers: int = 1,
    ) -> list[FlightResult]:
        dist = _get_distance(origin, destination)
        dur_low, dur_high = DURATION_RANGES[dist]

        price_ranges = {"short": (2000, 8000), "medium": (6000, 18000), "long": (12000, 40000)}
        p_low, p_high = price_ranges[dist]

        results = []
        # Generate 3-6 flights from random airlines
        num_flights = random.randint(3, 6)
        used = set()

        for _ in range(num_flights):
            airline_name, code = random.choice(self.AIRLINES)
            if code in used:
                continue
            used.add(code)

            duration = random.randint(dur_low, dur_high)
            dep_hour = random.randint(6, 21)
            dep_min = random.choice([0, 15, 30, 45])
            arr_total = dep_hour * 60 + dep_min + duration
            arr_hour = (arr_total // 60) % 24
            arr_min = arr_total % 60
            next_day = arr_total >= 24 * 60

            arr_date = travel_date
            if next_day:
                from datetime import timedelta
                arr_date = travel_date + timedelta(days=1)

            multiplier = 1.2 if travel_date.weekday() >= 5 else 1.0
            price = round(random.uniform(p_low, p_high) * multiplier)

            results.append(FlightResult(
                airline=airline_name,
                flight_number=f"{code}{random.randint(100, 999)}",
                origin=origin,
                destination=destination,
                departure_date=travel_date.isoformat(),
                departure_time=f"{dep_hour:02d}:{dep_min:02d}",
                arrival_date=arr_date.isoformat(),
                arrival_time=f"{arr_hour:02d}:{arr_min:02d}",
                duration_minutes=duration,
                price=price * passengers,
                source="simulated",
                is_direct=True,
                next_day=next_day,
            ))

        return sorted(results, key=lambda r: r.price)


class CrawlerRouter:
    """Routes search requests to multiple crawlers."""

    def __init__(self):
        self.crawlers: list[FlightCrawler] = []  # No SimulatedCrawler — real data only (US-17)

    def register(self, crawler: FlightCrawler):
        self.crawlers.append(crawler)

    async def search(
        self, origin: str, destination: str, travel_date: date, passengers: int = 1,
    ) -> tuple[list[FlightResult], list[str]]:
        """Search all crawlers in parallel. Returns (results, sources)."""
        tasks = [
            c.search(origin, destination, travel_date, passengers)
            for c in self.crawlers
        ]

        all_results: list[FlightResult] = []
        sources: list[str] = []

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        for crawler, result in zip(self.crawlers, results_list):
            if isinstance(result, Exception):
                continue  # Skip failed crawlers
            if result:
                all_results.extend(result)
                sources.append(crawler.name)

        return all_results, sources


# Global router instance
router = CrawlerRouter()

# Register real airline crawlers (they gracefully fail if Playwright not available)
try:
    from app.flights.evaair_crawler import EvaAirCrawler
    router.register(EvaAirCrawler())
except Exception:
    pass

try:
    from app.flights.starlux_crawler import StarluxCrawler
    router.register(StarluxCrawler())
except Exception:
    pass
