"""Ticket search service — orchestrates crawling, caching, and sorting.

Spec: specs/travel-planner-app/spec.md — US-1
Task: 1.5 — Search API + caching
"""

import json
from datetime import datetime

from app.tickets.crawler import get_crawler
from app.tickets.models import (
    FlightLeg,
    OutstationTicket,
    SortBy,
    TicketSearchRequest,
    TicketSearchResponse,
)
from app.tickets.outstation import generate_combinations


async def search_outstation_tickets(
    request: TicketSearchRequest,
    redis_client=None,
) -> TicketSearchResponse:
    """Search for outstation ticket combinations.

    1. Check Redis cache for existing results.
    2. If not cached, generate combinations and crawl prices.
    3. Sort results and return.
    """
    cache_key = _build_cache_key(request)

    # Check cache
    if redis_client:
        cached = await redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            resp = TicketSearchResponse(**data)
            resp.cached = True
            return resp

    # Generate outstation combinations
    combinations = generate_combinations(
        request.origin,
        request.destination,
        request.region_filter,
    )

    crawler = get_crawler()
    results: list[OutstationTicket] = []

    # Fetch direct flight price for comparison
    direct_leg = await crawler.fetch_price(
        request.origin, request.destination, request.departure_date, request.passengers
    )
    direct_return = await crawler.fetch_price(
        request.destination, request.origin, request.return_date, request.passengers
    )
    direct_price = None
    if direct_leg and direct_return:
        direct_price = (direct_leg.price + direct_return.price) * request.passengers

    # Fetch prices for each outstation combination
    for combo in combinations:
        legs: list[FlightLeg] = []
        total_price = 0
        total_transit = 0
        success = True

        leg_routes = combo["legs"]
        dates = [
            request.departure_date,  # Leg 1: outstation → origin
            request.departure_date,  # Leg 2: origin → destination
            request.return_date,     # Leg 3: destination → origin
            request.return_date,     # Leg 4: origin → outstation
        ]

        for route, travel_date in zip(leg_routes, dates):
            leg = await crawler.fetch_price(
                route["origin"],
                route["destination"],
                travel_date,
                request.passengers,
            )
            if leg is None:
                success = False
                break
            legs.append(leg)
            total_price += leg.price

        if not success:
            continue

        total_price_all = total_price * request.passengers

        savings = None
        savings_pct = None
        if direct_price and direct_price > 0:
            savings = direct_price - total_price_all
            savings_pct = round((savings / direct_price) * 100, 1)

        ticket = OutstationTicket(
            outstation_city=combo["outstation_code"],
            outstation_city_name=combo["outstation_name"],
            legs=legs,
            total_price=total_price_all,
            direct_price=direct_price,
            savings=savings,
            savings_percent=savings_pct,
            total_transit_time_minutes=total_transit,
        )

        # Apply max transit filter
        if request.max_transit_minutes and ticket.total_transit_time_minutes > request.max_transit_minutes:
            continue

        results.append(ticket)

    # Sort results
    results = _sort_results(results, request.sort_by)

    response = TicketSearchResponse(
        origin=request.origin,
        destination=request.destination,
        departure_date=request.departure_date,
        return_date=request.return_date,
        passengers=request.passengers,
        results=results,
        direct_price=direct_price,
        result_count=len(results),
        cached=False,
        searched_at=datetime.utcnow(),
    )

    # Cache results
    if redis_client:
        from app.core.config import settings
        await redis_client.setex(
            cache_key,
            settings.ticket_cache_ttl_seconds,
            response.model_dump_json(),
        )

    return response


def _sort_results(
    results: list[OutstationTicket],
    sort_by: SortBy,
) -> list[OutstationTicket]:
    if sort_by == SortBy.price:
        return sorted(results, key=lambda t: t.total_price)
    elif sort_by == SortBy.transit_time:
        return sorted(results, key=lambda t: t.total_transit_time_minutes)
    elif sort_by == SortBy.airline:
        return sorted(results, key=lambda t: t.legs[0].airline if t.legs else "")
    return results


def _build_cache_key(request: TicketSearchRequest) -> str:
    return (
        f"ticket_search:{request.origin}:{request.destination}"
        f":{request.departure_date}:{request.return_date}"
        f":{request.passengers}:{request.region_filter}"
    )
