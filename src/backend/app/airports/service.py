"""Airport search service — loads JSON, provides fuzzy search.

US-12: Global airport search
"""

import json
import re
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "airports.json"

_airports: list[dict] = []


def _load():
    global _airports
    if not _airports:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            _airports = json.load(f)
    return _airports


def search_airports(query: str, limit: int = 20) -> list[dict]:
    """Fuzzy search airports by IATA code, city name (zh/en), or country."""
    airports = _load()
    if not query or len(query.strip()) == 0:
        # Return popular airports
        return [a for a in airports if a.get("popular")][:limit]

    q = query.strip().upper()
    q_lower = query.strip().lower()

    exact = []
    starts = []
    contains = []

    for a in airports:
        iata = a["iata"]
        # Exact IATA match
        if iata == q:
            exact.append(a)
            continue

        # Check all searchable fields
        fields = [
            iata,
            a.get("city", ""),
            a.get("country", ""),
            a.get("city_zh", ""),
            a.get("country_zh", ""),
            a.get("name", ""),
        ]

        matched = False
        for field in fields:
            if not field:
                continue
            fl = field.lower()
            if fl.startswith(q_lower):
                starts.append(a)
                matched = True
                break
            elif q_lower in fl:
                contains.append(a)
                matched = True
                break

    # Combine: exact first, then starts-with, then contains
    # Within each group, popular airports first
    def sort_key(a):
        return (not a.get("popular", False), a["iata"])

    results = (
        sorted(exact, key=sort_key)
        + sorted(starts, key=sort_key)
        + sorted(contains, key=sort_key)
    )

    return results[:limit]


def get_airport(iata: str) -> dict | None:
    """Get a single airport by IATA code."""
    airports = _load()
    for a in airports:
        if a["iata"] == iata.upper():
            return a
    return None


def get_all_airports() -> list[dict]:
    """Get all airports (for frontend download)."""
    return _load()


def get_airport_count() -> int:
    return len(_load())
