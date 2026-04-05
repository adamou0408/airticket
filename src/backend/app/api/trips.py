"""Trip API endpoints.

Spec: specs/travel-planner-app/spec.md — US-3, US-4, US-5, US-6, US-7
Task: 2.3 — Trip CRUD API
Task: 2.4 — Invite and permission API
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.deps import get_current_user_id, get_optional_user_id
from app.trips.models import (
    CreateItemRequest,
    CreateTripRequest,
    InviteResponse,
    ItineraryItem,
    ReorderRequest,
    SetRoleRequest,
    TripDetail,
    TripSummary,
)
from app.trips.service import (
    add_item,
    can_edit,
    confirm_member,
    create_trip,
    delete_item,
    delete_trip,
    get_trip,
    get_trip_by_token,
    get_trip_detail,
    is_member,
    is_owner,
    join_trip,
    list_user_trips,
    reorder_items,
    set_member_role,
    update_item,
    update_trip,
)

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("", response_model=TripSummary, status_code=201)
async def create_new_trip(
    req: CreateTripRequest,
    user_id: int = Depends(get_current_user_id),
):
    """Create a new trip plan."""
    return create_trip(req, user_id)


@router.get("", response_model=list[TripSummary])
async def list_my_trips(user_id: int = Depends(get_current_user_id)):
    """List all trips the current user is a member of."""
    return list_user_trips(user_id)


@router.get("/{trip_id}", response_model=TripDetail)
async def get_trip_details(trip_id: int, user_id: int = Depends(get_current_user_id)):
    """Get full trip details including itinerary and members."""
    if not is_member(trip_id, user_id):
        raise HTTPException(status_code=403, detail="你不是這個旅遊計畫的成員")
    detail = get_trip_detail(trip_id)
    if not detail:
        raise HTTPException(status_code=404, detail="旅遊計畫不存在")
    return detail


@router.put("/{trip_id}", response_model=TripSummary)
async def update_trip_info(
    trip_id: int,
    req: CreateTripRequest,
    user_id: int = Depends(get_current_user_id),
):
    """Update trip basic info (owner only)."""
    if not is_owner(trip_id, user_id):
        raise HTTPException(status_code=403, detail="只有發起人可以修改計畫資訊")
    result = update_trip(
        trip_id,
        name=req.name,
        destination=req.destination,
        start_date=req.start_date,
        end_date=req.end_date,
        budget=req.budget,
    )
    if not result:
        raise HTTPException(status_code=404)
    return result


@router.delete("/{trip_id}", status_code=204)
async def remove_trip(trip_id: int, user_id: int = Depends(get_current_user_id)):
    """Delete a trip (owner only)."""
    if not is_owner(trip_id, user_id):
        raise HTTPException(status_code=403, detail="只有發起人可以刪除計畫")
    if not delete_trip(trip_id):
        raise HTTPException(status_code=404)


# --- Itinerary items ---

@router.post("/{trip_id}/items", response_model=ItineraryItem, status_code=201)
async def create_item(
    trip_id: int,
    req: CreateItemRequest,
    user_id: int = Depends(get_current_user_id),
):
    """Add an itinerary item to a trip."""
    if not can_edit(trip_id, user_id):
        raise HTTPException(status_code=403, detail="你沒有編輯權限")
    item = add_item(trip_id, req, user_id)
    if not item:
        raise HTTPException(status_code=404, detail="旅遊計畫不存在")
    return item


@router.put("/{trip_id}/items/{item_id}", response_model=ItineraryItem)
async def modify_item(
    trip_id: int,
    item_id: int,
    req: CreateItemRequest,
    user_id: int = Depends(get_current_user_id),
):
    """Update an itinerary item."""
    if not can_edit(trip_id, user_id):
        raise HTTPException(status_code=403, detail="你沒有編輯權限")
    result = update_item(item_id, **req.model_dump())
    if not result:
        raise HTTPException(status_code=404)
    return result


@router.delete("/{trip_id}/items/{item_id}", status_code=204)
async def remove_item(
    trip_id: int,
    item_id: int,
    user_id: int = Depends(get_current_user_id),
):
    """Delete an itinerary item."""
    if not can_edit(trip_id, user_id):
        raise HTTPException(status_code=403, detail="你沒有編輯權限")
    if not delete_item(item_id):
        raise HTTPException(status_code=404)


@router.put("/{trip_id}/items/reorder")
async def reorder_trip_items(
    trip_id: int,
    req: ReorderRequest,
    user_id: int = Depends(get_current_user_id),
):
    """Reorder itinerary items for a specific day."""
    if not can_edit(trip_id, user_id):
        raise HTTPException(status_code=403, detail="你沒有編輯權限")
    reorder_items(trip_id, 0, req.item_ids)
    return {"message": "排序已更新"}


# --- Invite / Join ---

@router.post("/{trip_id}/invite", response_model=InviteResponse)
async def generate_invite(
    trip_id: int,
    user_id: int = Depends(get_current_user_id),
):
    """Generate an invite link for the trip."""
    if not is_member(trip_id, user_id):
        raise HTTPException(status_code=403)
    trip = get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404)
    return InviteResponse(
        invite_link=f"/api/trips/join/{trip['share_token']}",
        share_token=trip["share_token"],
    )


@router.post("/join/{token}", response_model=TripSummary)
async def join_via_token(
    token: str,
    user_id: int | None = Depends(get_optional_user_id),
):
    """Join a trip via invite token."""
    trip = get_trip_by_token(token)
    if not trip:
        raise HTTPException(status_code=404, detail="邀請連結無效或已過期")
    if user_id:
        join_trip(trip["id"], user_id)
    from app.trips.service import _to_summary
    return _to_summary(trip)


@router.put("/{trip_id}/members/{target_user_id}", response_model=dict)
async def change_member_role(
    trip_id: int,
    target_user_id: int,
    req: SetRoleRequest,
    user_id: int = Depends(get_current_user_id),
):
    """Set a member's role (owner only)."""
    if not is_owner(trip_id, user_id):
        raise HTTPException(status_code=403, detail="只有發起人可以變更權限")
    if not set_member_role(trip_id, target_user_id, req.role):
        raise HTTPException(status_code=404)
    return {"message": "權限已更新"}


# --- Finalize ---

@router.post("/{trip_id}/confirm")
async def confirm_trip(
    trip_id: int,
    user_id: int = Depends(get_current_user_id),
):
    """Confirm finalization of the trip (each member must confirm)."""
    if not is_member(trip_id, user_id):
        raise HTTPException(status_code=403)
    confirm_member(trip_id, user_id)
    trip = get_trip(trip_id)
    return {
        "message": "已確認",
        "status": trip["status"] if trip else "unknown",
    }
