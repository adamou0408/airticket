"""Tests for Task 1.2: Ticket search data models."""

from datetime import date

from app.tickets.models import (
    FlightLeg,
    OutstationTicket,
    TicketSearchRequest,
    TicketSearchResponse,
    SortBy,
)


def test_flight_leg_creation():
    leg = FlightLeg(origin="HKG", destination="TPE", airline="CX")
    assert leg.origin == "HKG"
    assert leg.destination == "TPE"
    assert leg.airline == "CX"


def test_outstation_ticket_4_legs():
    legs = [
        FlightLeg(origin="HKG", destination="TPE", airline="CX", price=3000),
        FlightLeg(origin="TPE", destination="NRT", airline="CX", price=5000),
        FlightLeg(origin="NRT", destination="TPE", airline="CX", price=5000),
        FlightLeg(origin="TPE", destination="HKG", airline="CX", price=3000),
    ]
    ticket = OutstationTicket(
        outstation_city="HKG",
        outstation_city_name="Hong Kong",
        legs=legs,
        total_price=16000,
        direct_price=20000,
        savings=4000,
        savings_percent=20.0,
        total_transit_time_minutes=120,
    )
    assert len(ticket.legs) == 4
    assert ticket.total_price == 16000
    assert ticket.savings == 4000
    assert ticket.savings_percent == 20.0


def test_search_request_defaults():
    req = TicketSearchRequest(
        origin="TPE",
        destination="NRT",
        departure_date=date(2026, 7, 1),
        return_date=date(2026, 7, 10),
    )
    assert req.passengers == 1
    assert req.sort_by == SortBy.price
    assert req.region_filter is None


def test_search_response():
    resp = TicketSearchResponse(
        origin="TPE",
        destination="NRT",
        departure_date=date(2026, 7, 1),
        return_date=date(2026, 7, 10),
        passengers=2,
        results=[],
        result_count=0,
    )
    assert resp.passengers == 2
    assert resp.results == []
