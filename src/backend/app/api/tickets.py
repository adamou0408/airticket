"""Ticket search API endpoints.

Spec: specs/travel-planner-app/spec.md — US-1
Task: 1.5 — Search API + caching
"""

from fastapi import APIRouter

from app.tickets.models import TicketSearchRequest, TicketSearchResponse
from app.tickets.service import search_outstation_tickets

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/search", response_model=TicketSearchResponse)
async def search_tickets(request: TicketSearchRequest):
    """Search for outstation (4-leg) ticket combinations.

    Returns ticket combinations sorted by price (default),
    with direct flight price comparison.
    """
    return await search_outstation_tickets(request, redis_client=None)
