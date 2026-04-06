"""Flight search service — orchestrates crawler router, caching, sorting.

US-13: One-way search
US-14: Round-trip search
"""

from app.flights.crawler_router import router as crawler_router
from app.flights.models import (
    FlightResult, FlightSearchRequest, FlightSearchResponse, SortBy, TripType,
)


async def search_flights(request: FlightSearchRequest) -> FlightSearchResponse:
    """Search for one-way or round-trip flights."""

    # Search outbound
    outbound, out_sources = await crawler_router.search(
        request.origin, request.destination, request.departure_date, request.passengers,
    )
    outbound = _sort(outbound, request.sort_by)

    # Search return (if round-trip)
    return_flights: list[FlightResult] = []
    ret_sources: list[str] = []
    if request.trip_type == TripType.round_trip and request.return_date:
        return_flights, ret_sources = await crawler_router.search(
            request.destination, request.origin, request.return_date, request.passengers,
        )
        return_flights = _sort(return_flights, request.sort_by)

    all_sources = list(set(out_sources + ret_sources))

    cheapest_out = min((f.price for f in outbound), default=None)
    cheapest_ret = min((f.price for f in return_flights), default=None)
    cheapest_rt = (cheapest_out + cheapest_ret) if cheapest_out and cheapest_ret else None

    return FlightSearchResponse(
        origin=request.origin,
        destination=request.destination,
        trip_type=request.trip_type,
        departure_date=request.departure_date.isoformat(),
        return_date=request.return_date.isoformat() if request.return_date else None,
        passengers=request.passengers,
        outbound_flights=outbound,
        return_flights=return_flights,
        cheapest_outbound=cheapest_out,
        cheapest_return=cheapest_ret,
        cheapest_roundtrip=cheapest_rt,
        result_count=len(outbound) + len(return_flights),
        sources=all_sources,
    )


def _sort(flights: list[FlightResult], sort_by: SortBy) -> list[FlightResult]:
    if sort_by == SortBy.price:
        return sorted(flights, key=lambda f: f.price)
    elif sort_by == SortBy.departure:
        return sorted(flights, key=lambda f: f.departure_time)
    elif sort_by == SortBy.duration:
        return sorted(flights, key=lambda f: f.duration_minutes)
    elif sort_by == SortBy.airline:
        return sorted(flights, key=lambda f: f.airline)
    return flights
