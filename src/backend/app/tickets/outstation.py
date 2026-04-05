"""Outstation (4-leg) ticket combination algorithm.

Spec: specs/travel-planner-app/spec.md — US-1
Task: 1.3 — Outstation ticket combination algorithm

An outstation ticket (外站票/四段票) works like this:
- Instead of flying directly Origin → Destination (round trip = 2 legs),
  you book a round trip FROM a cheaper city (the "outstation"):

  Leg 1: Outstation → Origin       (you fly TO your actual departure city)
  Leg 2: Origin → Destination      (your actual outbound flight)
  Leg 3: Destination → Origin      (your actual return flight)
  Leg 4: Origin → Outstation       (you fly BACK to the outstation city)

  The total of 4 legs is often cheaper than a direct round-trip
  Origin → Destination because airline pricing varies by origin city.
"""

# Common outstation cities grouped by region.
# These are cities where flights often originate at lower prices.
OUTSTATION_CITIES: dict[str, list[dict[str, str]]] = {
    "northeast_asia": [
        {"code": "HKG", "name": "香港"},
        {"code": "MFM", "name": "澳門"},
        {"code": "NRT", "name": "東京成田"},
        {"code": "KIX", "name": "大阪關西"},
        {"code": "ICN", "name": "首爾仁川"},
        {"code": "PVG", "name": "上海浦東"},
    ],
    "southeast_asia": [
        {"code": "BKK", "name": "曼谷"},
        {"code": "SIN", "name": "新加坡"},
        {"code": "KUL", "name": "吉隆坡"},
        {"code": "MNL", "name": "馬尼拉"},
        {"code": "SGN", "name": "胡志明市"},
        {"code": "HAN", "name": "河內"},
    ],
    "other": [
        {"code": "SFO", "name": "舊金山"},
        {"code": "LAX", "name": "洛杉磯"},
        {"code": "LHR", "name": "倫敦"},
        {"code": "SYD", "name": "雪梨"},
    ],
}


def get_outstation_cities(
    origin: str,
    destination: str,
    region_filter: str | None = None,
) -> list[dict[str, str]]:
    """Return candidate outstation cities, excluding origin and destination.

    Args:
        origin: The actual departure airport code (e.g. "TPE").
        destination: The destination airport code (e.g. "NRT").
        region_filter: Optional region key to limit results.

    Returns:
        List of city dicts with "code" and "name" keys.
    """
    if region_filter and region_filter in OUTSTATION_CITIES:
        regions = {region_filter: OUTSTATION_CITIES[region_filter]}
    else:
        regions = OUTSTATION_CITIES

    cities = []
    seen = set()
    for region_cities in regions.values():
        for city in region_cities:
            code = city["code"]
            # Exclude origin and destination — they can't be outstations
            if code not in (origin, destination) and code not in seen:
                cities.append(city)
                seen.add(code)
    return cities


def build_outstation_legs(
    origin: str,
    destination: str,
    outstation_code: str,
) -> list[dict[str, str]]:
    """Build the 4 flight legs for an outstation ticket.

    Args:
        origin: Actual departure city (e.g. "TPE").
        destination: Final destination (e.g. "CDG").
        outstation_code: The outstation city (e.g. "HKG").

    Returns:
        List of 4 dicts, each with "origin" and "destination" keys.
    """
    return [
        {"origin": outstation_code, "destination": origin},       # Leg 1: outstation → origin
        {"origin": origin, "destination": destination},            # Leg 2: origin → destination
        {"origin": destination, "destination": origin},            # Leg 3: destination → origin
        {"origin": origin, "destination": outstation_code},        # Leg 4: origin → outstation
    ]


def generate_combinations(
    origin: str,
    destination: str,
    region_filter: str | None = None,
) -> list[dict]:
    """Generate all outstation ticket combinations.

    Args:
        origin: Departure city code.
        destination: Destination city code.
        region_filter: Optional region filter.

    Returns:
        List of combination dicts with outstation info and leg routes.
    """
    cities = get_outstation_cities(origin, destination, region_filter)
    combinations = []

    for city in cities:
        legs = build_outstation_legs(origin, destination, city["code"])
        combinations.append({
            "outstation_code": city["code"],
            "outstation_name": city["name"],
            "legs": legs,
        })

    return combinations
