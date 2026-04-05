"""Trip service — in-memory store for MVP.

Task: 2.2-2.4
"""

import secrets
from datetime import datetime

from app.trips.models import (
    CreateItemRequest,
    CreateTripRequest,
    ItineraryItem,
    MemberRole,
    TripDetail,
    TripMember,
    TripStatus,
    TripSummary,
)

# In-memory stores
_trips: dict[int, dict] = {}
_items: dict[int, dict] = {}  # item_id -> item data
_next_trip_id = 1
_next_item_id = 1


def _reset():
    """Reset stores (for testing)."""
    global _next_trip_id, _next_item_id
    _trips.clear()
    _items.clear()
    _next_trip_id = 1
    _next_item_id = 1


def create_trip(req: CreateTripRequest, owner_id: int) -> TripSummary:
    global _next_trip_id
    token = secrets.token_urlsafe(16)
    trip = {
        "id": _next_trip_id,
        "name": req.name,
        "destination": req.destination,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "budget": req.budget,
        "currency": req.currency,
        "status": TripStatus.planning,
        "owner_id": owner_id,
        "share_token": token,
        "members": {owner_id: {"user_id": owner_id, "name": "", "role": MemberRole.owner, "confirmed": True}},
    }
    _trips[_next_trip_id] = trip
    _next_trip_id += 1
    return _to_summary(trip)


def get_trip(trip_id: int) -> dict | None:
    return _trips.get(trip_id)


def get_trip_detail(trip_id: int) -> TripDetail | None:
    trip = _trips.get(trip_id)
    if not trip:
        return None
    items = sorted(
        [_to_item(i) for i in _items.values() if i["trip_id"] == trip_id],
        key=lambda x: (x.day_number, x.order),
    )
    return TripDetail(
        **{k: v for k, v in trip.items() if k != "members"},
        members=[TripMember(**m) for m in trip["members"].values()],
        items=items,
    )


def list_user_trips(user_id: int) -> list[TripSummary]:
    result = []
    for trip in _trips.values():
        if user_id in trip["members"]:
            result.append(_to_summary(trip))
    return result


def update_trip(trip_id: int, **kwargs) -> TripSummary | None:
    trip = _trips.get(trip_id)
    if not trip:
        return None
    for k, v in kwargs.items():
        if k in trip and v is not None:
            trip[k] = v
    return _to_summary(trip)


def delete_trip(trip_id: int) -> bool:
    if trip_id in _trips:
        del _trips[trip_id]
        # Remove associated items
        to_remove = [iid for iid, i in _items.items() if i["trip_id"] == trip_id]
        for iid in to_remove:
            del _items[iid]
        return True
    return False


def add_item(trip_id: int, req: CreateItemRequest, user_id: int) -> ItineraryItem | None:
    global _next_item_id
    if trip_id not in _trips:
        return None
    existing = [i for i in _items.values() if i["trip_id"] == trip_id and i["day_number"] == req.day_number]
    order = len(existing) + 1
    item = {
        "id": _next_item_id,
        "trip_id": trip_id,
        "day_number": req.day_number,
        "order": order,
        "type": req.type,
        "name": req.name,
        "time": req.time,
        "location": req.location,
        "note": req.note,
        "estimated_cost": req.estimated_cost,
        "created_by": user_id,
    }
    _items[_next_item_id] = item
    _next_item_id += 1
    return _to_item(item)


def update_item(item_id: int, **kwargs) -> ItineraryItem | None:
    item = _items.get(item_id)
    if not item:
        return None
    for k, v in kwargs.items():
        if k in item and v is not None:
            item[k] = v
    return _to_item(item)


def delete_item(item_id: int) -> bool:
    if item_id in _items:
        del _items[item_id]
        return True
    return False


def reorder_items(trip_id: int, day_number: int, item_ids: list[int]) -> bool:
    for order, iid in enumerate(item_ids, 1):
        item = _items.get(iid)
        if item and item["trip_id"] == trip_id:
            item["order"] = order
    return True


# --- Invite / Permission ---

def get_trip_by_token(token: str) -> dict | None:
    for trip in _trips.values():
        if trip["share_token"] == token:
            return trip
    return None


def join_trip(trip_id: int, user_id: int, role: MemberRole = MemberRole.editor) -> bool:
    trip = _trips.get(trip_id)
    if not trip:
        return False
    if user_id not in trip["members"]:
        trip["members"][user_id] = {"user_id": user_id, "name": "", "role": role, "confirmed": False}
    return True


def set_member_role(trip_id: int, target_user_id: int, role: MemberRole) -> bool:
    trip = _trips.get(trip_id)
    if not trip or target_user_id not in trip["members"]:
        return False
    trip["members"][target_user_id]["role"] = role
    return True


def is_member(trip_id: int, user_id: int) -> bool:
    trip = _trips.get(trip_id)
    return trip is not None and user_id in trip["members"]


def is_owner(trip_id: int, user_id: int) -> bool:
    trip = _trips.get(trip_id)
    return trip is not None and trip["owner_id"] == user_id


def can_edit(trip_id: int, user_id: int) -> bool:
    trip = _trips.get(trip_id)
    if not trip:
        return False
    member = trip["members"].get(user_id)
    if not member:
        return False
    return member["role"] in (MemberRole.owner, MemberRole.editor)


# --- Finalize ---

def confirm_member(trip_id: int, user_id: int) -> bool:
    trip = _trips.get(trip_id)
    if not trip or user_id not in trip["members"]:
        return False
    trip["members"][user_id]["confirmed"] = True
    # Check if all members confirmed
    if all(m["confirmed"] for m in trip["members"].values()):
        trip["status"] = TripStatus.finalized
    return True


def unlock_trip(trip_id: int) -> bool:
    """Unlock a finalized trip back to planning status."""
    trip = _trips.get(trip_id)
    if not trip:
        return False
    trip["status"] = TripStatus.planning
    # Reset all confirmations
    for m in trip["members"].values():
        m["confirmed"] = False
    return True


def is_finalized(trip_id: int) -> bool:
    trip = _trips.get(trip_id)
    return trip is not None and trip["status"] == TripStatus.finalized


def _to_summary(trip: dict) -> TripSummary:
    return TripSummary(
        id=trip["id"],
        name=trip["name"],
        destination=trip["destination"],
        start_date=trip["start_date"],
        end_date=trip["end_date"],
        budget=trip["budget"],
        currency=trip["currency"],
        status=trip["status"],
        owner_id=trip["owner_id"],
        member_count=len(trip["members"]),
        share_token=trip["share_token"],
    )


def _to_item(item: dict) -> ItineraryItem:
    return ItineraryItem(
        id=item["id"],
        day_number=item["day_number"],
        order=item["order"],
        type=item["type"],
        name=item["name"],
        time=item["time"],
        location=item["location"],
        note=item["note"],
        estimated_cost=item["estimated_cost"],
        created_by=item["created_by"],
    )
