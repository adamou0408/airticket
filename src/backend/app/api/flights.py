"""Flight search API endpoints.

US-13: One-way search
US-14: Round-trip search
"""

from fastapi import APIRouter

from app.flights.models import FlightSearchRequest, FlightSearchResponse
from app.flights.service import search_flights

router = APIRouter(prefix="/flights", tags=["flights"])


@router.post("/search", response_model=FlightSearchResponse)
async def search(request: FlightSearchRequest):
    """Search for one-way or round-trip flights."""
    return await search_flights(request)
