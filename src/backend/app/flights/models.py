"""Flight search models — one-way and round-trip.

US-13, US-14, US-15
"""

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class TripType(str, Enum):
    one_way = "one_way"
    round_trip = "round_trip"


class SortBy(str, Enum):
    price = "price"
    departure = "departure"
    duration = "duration"
    airline = "airline"


class FlightStop(BaseModel):
    city: str
    city_name: str = ""
    wait_minutes: int = 0
    wait_display: str = ""


class FlightResult(BaseModel):
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure_date: str
    departure_time: str
    arrival_date: str
    arrival_time: str
    duration_minutes: int
    price: float
    currency: str = "TWD"
    stops: list[FlightStop] = []
    is_direct: bool = True
    source: str = "simulated"  # "evaair" | "starlux" | "simulated"
    next_day: bool = False


class FlightSearchRequest(BaseModel):
    origin: str = Field(..., examples=["TPE"])
    destination: str = Field(..., examples=["NRT"])
    departure_date: date
    return_date: date | None = None  # None = one-way
    passengers: int = Field(1, ge=1, le=9)
    trip_type: TripType = TripType.round_trip
    sort_by: SortBy = SortBy.price


class FlightSearchResponse(BaseModel):
    origin: str
    destination: str
    trip_type: TripType
    departure_date: str
    return_date: str | None
    passengers: int
    outbound_flights: list[FlightResult]
    return_flights: list[FlightResult]  # empty for one-way
    cheapest_outbound: float | None = None
    cheapest_return: float | None = None
    cheapest_roundtrip: float | None = None
    result_count: int = 0
    sources: list[str] = []  # which crawlers returned data
    cached: bool = False
