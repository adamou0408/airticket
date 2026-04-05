"""Share and export API endpoints.

Spec: specs/travel-planner-app/spec.md — US-8, US-11
Task: 5.1 — Trip export
Task: 5.2 — Read-only share link
Task: 5.3 — Settlement sharing
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from app.auth.deps import get_current_user_id
from app.trips.service import get_trip, is_member
from app.trips.share import (
    export_settlement_text,
    export_trip_json,
    export_trip_text,
    get_shared_trip,
)

router = APIRouter(tags=["share"])


# --- Task 5.1: Trip export ---

@router.get("/trips/{trip_id}/export/text", response_class=PlainTextResponse)
async def export_text(trip_id: int, user_id: int = Depends(get_current_user_id)):
    """Export trip as formatted plain text."""
    if not is_member(trip_id, user_id):
        raise HTTPException(status_code=403)
    result = export_trip_text(trip_id)
    if not result:
        raise HTTPException(status_code=404)
    return result


@router.get("/trips/{trip_id}/export/json")
async def export_json(trip_id: int, user_id: int = Depends(get_current_user_id)):
    """Export trip as structured JSON (for frontend PDF/image generation)."""
    if not is_member(trip_id, user_id):
        raise HTTPException(status_code=403)
    result = export_trip_json(trip_id)
    if not result:
        raise HTTPException(status_code=404)
    return result


# --- Task 5.2: Read-only share link (no auth required) ---

@router.get("/share/{share_token}")
async def view_shared_trip(share_token: str):
    """View a trip via share link — no authentication required."""
    result = get_shared_trip(share_token)
    if not result:
        raise HTTPException(status_code=404, detail="分享連結無效或已過期")
    return result


# --- Task 5.3: Settlement export ---

@router.get("/trips/{trip_id}/settlement/export/text", response_class=PlainTextResponse)
async def export_settlement(trip_id: int, user_id: int = Depends(get_current_user_id)):
    """Export settlement result as formatted text for sharing."""
    if not is_member(trip_id, user_id):
        raise HTTPException(status_code=403)
    result = export_settlement_text(trip_id)
    if not result:
        raise HTTPException(status_code=404)
    return result
