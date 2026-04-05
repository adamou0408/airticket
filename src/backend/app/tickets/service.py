"""Ticket search service — orchestrates crawling, caching, and sorting.

Spec: specs/travel-planner-app/spec.md — US-1
Task: 1.5 — Search API + caching
Iterate: 2026-04-05 — Added layover calculation and total journey time
"""

import json
from datetime import datetime

from app.tickets.crawler import get_crawler
from app.tickets.models import (
    FlightLeg,
    LayoverInfo,
    OutstationTicket,
    SortBy,
    TicketSearchRequest,
    TicketSearchResponse,
)
from app.tickets.outstation import generate_combinations


def _format_duration(minutes: int) -> str:
    """Format minutes as 'Xh Ym'."""
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"


def _time_to_minutes(time_str: str) -> int:
    """Convert HH:MM to minutes since midnight."""
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def _calculate_layover(prev_leg: FlightLeg, next_leg: FlightLeg) -> LayoverInfo:
    """Calculate layover between two consecutive legs."""
    arr_min = _time_to_minutes(prev_leg.arrival_time)
    dep_min = _time_to_minutes(next_leg.departure_time)

    wait = dep_min - arr_min
    if wait < 0:
        wait += 24 * 60  # crosses midnight

    return LayoverInfo(
        city=prev_leg.destination,
        duration_minutes=wait,
        duration_display=_format_duration(wait),
    )


def _calculate_segment_hours(legs: list[FlightLeg], layovers: list[LayoverInfo], start: int, end: int) -> float:
    """Calculate total hours for a segment of legs (inclusive)."""
    total_min = 0
    for i in range(start, end + 1):
        total_min += legs[i].flight_duration_minutes
    for i in range(start, end):
        # layover index between leg i and leg i+1
        if i < len(layovers):
            total_min += layovers[i].duration_minutes
    return round(total_min / 60, 1)


async def search_outstation_tickets(
    request: TicketSearchRequest,
    redis_client=None,
) -> TicketSearchResponse:
    cache_key = _build_cache_key(request)

    if redis_client:
        cached = await redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            resp = TicketSearchResponse(**data)
            resp.cached = True
            return resp

    combinations = generate_combinations(
        request.origin, request.destination, request.region_filter,
    )

    crawler = get_crawler()
    results: list[OutstationTicket] = []

    # Direct flight price for comparison
    direct_leg = await crawler.fetch_price(
        request.origin, request.destination, request.departure_date, request.passengers
    )
    direct_return = await crawler.fetch_price(
        request.destination, request.origin, request.return_date, request.passengers
    )
    direct_price = None
    if direct_leg and direct_return:
        direct_price = (direct_leg.price + direct_return.price) * request.passengers

    for combo in combinations:
        legs: list[FlightLeg] = []
        total_price = 0
        success = True

        leg_routes = combo["legs"]
        dates = [
            request.departure_date,
            request.departure_date,
            request.return_date,
            request.return_date,
        ]

        for route, travel_date in zip(leg_routes, dates):
            leg = await crawler.fetch_price(
                route["origin"], route["destination"], travel_date, request.passengers,
            )
            if leg is None:
                success = False
                break
            legs.append(leg)
            total_price += leg.price

        if not success:
            continue

        # Calculate layovers between consecutive legs
        layovers = []
        for i in range(len(legs) - 1):
            # Only calculate layover between leg 0→1 and leg 2→3
            # (legs 1 and 2 are separated by the trip itself, not a layover)
            if i == 0 or i == 2:
                layover = _calculate_layover(legs[i], legs[i + 1])
                layovers.append(layover)

        total_transit = sum(l.duration_minutes for l in layovers)
        total_flight = sum(l.flight_duration_minutes for l in legs)

        outbound_min = legs[0].flight_duration_minutes + (layovers[0].duration_minutes if layovers else 0) + legs[1].flight_duration_minutes
        return_min = legs[2].flight_duration_minutes + (layovers[1].duration_minutes if len(layovers) > 1 else 0) + legs[3].flight_duration_minutes

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
            layovers=layovers,
            total_price=total_price_all,
            direct_price=direct_price,
            savings=savings,
            savings_percent=savings_pct,
            total_transit_time_minutes=total_transit,
            total_journey_hours=round((total_flight + total_transit) / 60, 1),
            outbound_hours=round(outbound_min / 60, 1),
            return_hours=round(return_min / 60, 1),
        )

        if request.max_transit_minutes and ticket.total_transit_time_minutes > request.max_transit_minutes:
            continue

        results.append(ticket)

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

    if redis_client:
        from app.core.config import settings
        await redis_client.setex(cache_key, settings.ticket_cache_ttl_seconds, response.model_dump_json())

    return response


def _sort_results(results: list[OutstationTicket], sort_by: SortBy) -> list[OutstationTicket]:
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
