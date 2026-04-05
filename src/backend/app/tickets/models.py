"""Ticket search data models.

Spec: specs/travel-planner-app/spec.md — US-1
Task: 1.2 — Data models for ticket search
Iterate: 2026-04-05 — Added timeline fields (datetime, duration, layover)
"""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class SortBy(str, Enum):
    price = "price"
    transit_time = "transit_time"
    airline = "airline"


class FlightLeg(BaseModel):
    """A single flight segment with full time information."""
    origin: str = Field(..., description="Departure airport code (e.g. TPE)")
    destination: str = Field(..., description="Arrival airport code (e.g. NRT)")
    airline: str = Field(..., description="Airline name or code")
    flight_number: str = ""
    departure_time: str = Field("", description="Departure time HH:MM")
    arrival_time: str = Field("", description="Arrival time HH:MM")
    departure_date: str = Field("", description="Departure date YYYY-MM-DD")
    arrival_date: str = Field("", description="Arrival date YYYY-MM-DD (may differ if overnight)")
    flight_duration_minutes: int = Field(0, description="Flight duration in minutes")
    price: float = 0
    next_day: bool = Field(False, description="Arrives next day (+1)")


class LayoverInfo(BaseModel):
    """Layover/transit between two legs."""
    city: str = Field(..., description="Layover city code")
    duration_minutes: int = Field(..., description="Wait time in minutes")
    duration_display: str = Field("", description="e.g. '3h 20m'")


class OutstationTicket(BaseModel):
    """A complete outstation (4-leg) ticket combination with timeline."""
    outstation_city: str = Field(..., description="The outstation city code")
    outstation_city_name: str = Field("", description="The outstation city name")
    legs: list[FlightLeg] = Field(..., min_length=4, max_length=4)
    layovers: list[LayoverInfo] = Field(default_factory=list, description="Layover info between legs")
    total_price: float = Field(..., description="Total price for all 4 legs")
    direct_price: float | None = Field(None, description="Direct flight price for comparison")
    savings: float | None = Field(None, description="Amount saved vs direct")
    savings_percent: float | None = Field(None, description="Percentage saved")
    total_transit_time_minutes: int = Field(0, description="Total layover time")
    total_journey_hours: float = Field(0, description="Total hours from first departure to last arrival")
    outbound_hours: float = Field(0, description="Hours for legs 1+2 (outstation→origin→dest)")
    return_hours: float = Field(0, description="Hours for legs 3+4 (dest→origin→outstation)")
    currency: str = "TWD"


class TicketSearchRequest(BaseModel):
    """Request body for ticket search."""
    origin: str = Field(..., description="Departure city/airport code", examples=["TPE"])
    destination: str = Field(..., description="Destination city/airport code", examples=["NRT"])
    departure_date: date
    return_date: date
    passengers: int = Field(1, ge=1, le=9)
    sort_by: SortBy = SortBy.price
    region_filter: str | None = Field(None, description="Filter outstation cities by region")
    max_transit_minutes: int | None = Field(None, description="Max transit time filter")


class TicketSearchResponse(BaseModel):
    """Response for ticket search."""
    origin: str
    destination: str
    departure_date: date
    return_date: date
    passengers: int
    results: list[OutstationTicket]
    direct_price: float | None = None
    result_count: int = 0
    cached: bool = False
    searched_at: datetime | None = None
