"""Ticket search data models.

Spec: specs/travel-planner-app/spec.md — US-1
Task: 1.2 — Data models for ticket search
"""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class SortBy(str, Enum):
    price = "price"
    transit_time = "transit_time"
    airline = "airline"


class FlightLeg(BaseModel):
    """A single flight segment."""
    origin: str = Field(..., description="Departure airport code (e.g. TPE)")
    destination: str = Field(..., description="Arrival airport code (e.g. NRT)")
    airline: str = Field(..., description="Airline name or code")
    flight_number: str = ""
    departure_time: str = ""
    arrival_time: str = ""
    price: float = 0


class OutstationTicket(BaseModel):
    """A complete outstation (4-leg) ticket combination.

    Four legs:
    1. Outstation → Origin (去程: 外站 → 出發地)
    2. Origin → Destination (去程: 出發地 → 目的地)
    3. Destination → Origin (回程: 目的地 → 出發地)
    4. Origin → Outstation (回程: 出發地 → 外站)
    """
    outstation_city: str = Field(..., description="The outstation city code")
    outstation_city_name: str = Field("", description="The outstation city name for display")
    legs: list[FlightLeg] = Field(..., min_length=4, max_length=4)
    total_price: float = Field(..., description="Total price for all 4 legs")
    direct_price: float | None = Field(None, description="Direct flight price for comparison")
    savings: float | None = Field(None, description="Amount saved vs direct flight")
    savings_percent: float | None = Field(None, description="Percentage saved vs direct")
    total_transit_time_minutes: int = Field(0, description="Total transit/layover time in minutes")
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
