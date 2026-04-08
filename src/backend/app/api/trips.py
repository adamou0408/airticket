"""Trip API endpoints — database-backed."""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user_id, get_optional_user_id
from app.auth.service import decode_access_token
from app.core.database import get_db, async_session
from app.trips import comments as comments_mod
from app.trips.comments import CommentCreate
from app.trips.models import (
    CreateItemRequest, CreateTripRequest, InviteResponse,
    ReorderRequest, SetRoleRequest,
)
from app.trips import service as trip_svc
from app.trips import websocket as ws_svc

router = APIRouter(prefix="/trips", tags=["trips"])


# ─── Helpers ─────────────────────────────────────────

def _trip_to_summary(trip):
    return {
        "id": trip.id, "name": trip.name, "destination": trip.destination,
        "start_date": trip.start_date, "end_date": trip.end_date,
        "budget": trip.budget, "currency": trip.currency,
        "status": trip.status, "owner_id": trip.owner_id,
        "member_count": len(trip.members), "share_token": trip.share_token,
    }


def _trip_to_detail(trip):
    return {
        **_trip_to_summary(trip),
        "members": [{"user_id": m.user_id, "name": "", "role": m.role, "confirmed": m.confirmed} for m in trip.members],
        "items": sorted([{
            "id": i.id, "day_number": i.day_number, "order": i.order,
            "type": i.type, "name": i.name, "time": i.time,
            "location": i.location, "note": i.note,
            "estimated_cost": i.estimated_cost, "created_by": i.created_by,
        } for i in trip.items], key=lambda x: (x["day_number"], x["order"])),
    }


def _item_to_dict(item):
    return {
        "id": item.id, "day_number": item.day_number, "order": item.order,
        "type": item.type, "name": item.name, "time": item.time,
        "location": item.location, "note": item.note,
        "estimated_cost": item.estimated_cost, "created_by": item.created_by,
    }


async def _get_trip_or_404(db: AsyncSession, trip_id: int):
    trip = await trip_svc.get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="旅遊計畫不存在")
    return trip


# ─── Trip CRUD ───────────────────────────────────────

@router.post("", status_code=201)
async def create_new_trip(req: CreateTripRequest, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await trip_svc.create_trip(db, req.name, req.destination, req.start_date, req.end_date, req.budget, req.currency, user_id)
    return _trip_to_summary(trip)


@router.get("")
async def list_my_trips(user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trips = await trip_svc.list_user_trips(db, user_id)
    return [_trip_to_summary(t) for t in trips]


@router.get("/{trip_id}")
async def get_trip_details(trip_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.is_member(trip, user_id):
        raise HTTPException(status_code=403, detail="你不是這個旅遊計畫的成員")
    return _trip_to_detail(trip)


@router.put("/{trip_id}")
async def update_trip_info(trip_id: int, req: CreateTripRequest, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.is_owner(trip, user_id):
        raise HTTPException(status_code=403, detail="只有發起人可以修改")
    updated = await trip_svc.update_trip(db, trip_id, name=req.name, destination=req.destination, start_date=req.start_date, end_date=req.end_date, budget=req.budget)
    return _trip_to_summary(updated)


@router.delete("/{trip_id}", status_code=204)
async def remove_trip(trip_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.is_owner(trip, user_id):
        raise HTTPException(status_code=403, detail="只有發起人可以刪除")
    await trip_svc.delete_trip(db, trip_id)


# ─── Items ───────────────────────────────────────────

@router.post("/{trip_id}/items/from-flight", status_code=201)
async def add_from_flight(trip_id: int, flights: list[dict], user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """Add flight(s) as itinerary items — one-click from search results (US-20)."""
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.can_edit(trip, user_id):
        raise HTTPException(status_code=403, detail="你沒有編輯權限")
    items = []
    for f in flights:
        name = f"{f.get('airline','')} {f.get('flight_number','')}".strip()
        time = f.get('departure_time', '')
        cost = f.get('price', 0)
        day = 1  # Default to day 1
        item = await trip_svc.add_item(db, trip_id, day, 'transport', name, time, f"{f.get('origin','')}-{f.get('destination','')}", '', cost, user_id)
        items.append(_item_to_dict(item))
    return items


@router.post("/{trip_id}/items", status_code=201)
async def create_item(trip_id: int, req: CreateItemRequest, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.can_edit(trip, user_id):
        raise HTTPException(status_code=403, detail="你沒有編輯權限")
    item = await trip_svc.add_item(db, trip_id, req.day_number, req.type, req.name, req.time, req.location, req.note, req.estimated_cost, user_id)
    item_dict = _item_to_dict(item)
    await ws_svc.notify_item_added(trip_id, item_dict, user_id)
    return item_dict


@router.put("/{trip_id}/items/{item_id}")
async def modify_item(trip_id: int, item_id: int, req: CreateItemRequest, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.can_edit(trip, user_id):
        raise HTTPException(status_code=403, detail="你沒有編輯權限")
    item = await trip_svc.update_item(db, item_id, day_number=req.day_number, type=req.type, name=req.name, time=req.time, location=req.location, note=req.note, estimated_cost=req.estimated_cost)
    if not item:
        raise HTTPException(status_code=404)
    item_dict = _item_to_dict(item)
    await ws_svc.notify_item_updated(trip_id, item_dict, user_id)
    return item_dict


@router.delete("/{trip_id}/items/{item_id}", status_code=204)
async def remove_item(trip_id: int, item_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.can_edit(trip, user_id):
        raise HTTPException(status_code=403, detail="你沒有編輯權限")
    await trip_svc.delete_item(db, item_id)
    await ws_svc.notify_item_deleted(trip_id, item_id, user_id)


@router.put("/{trip_id}/items/reorder")
async def reorder_trip_items(trip_id: int, req: ReorderRequest, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.can_edit(trip, user_id):
        raise HTTPException(status_code=403, detail="你沒有編輯權限")
    await trip_svc.reorder_items(db, trip_id, req.item_ids)
    return {"message": "排序已更新"}


# ─── Invite / Join ───────────────────────────────────

@router.post("/{trip_id}/invite")
async def generate_invite(trip_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.is_member(trip, user_id):
        raise HTTPException(status_code=403)
    return InviteResponse(invite_link=f"/api/trips/join/{trip.share_token}", share_token=trip.share_token)


@router.post("/join/{token}")
async def join_via_token(token: str, user_id: int | None = Depends(get_optional_user_id), db: AsyncSession = Depends(get_db)):
    trip = await trip_svc.get_trip_by_token(db, token)
    if not trip:
        raise HTTPException(status_code=404, detail="邀請連結無效或已過期")
    if user_id:
        await trip_svc.join_trip(db, trip.id, user_id)
        await db.refresh(trip, ["members"])
    return _trip_to_summary(trip)


@router.put("/{trip_id}/members/{target_user_id}")
async def change_member_role(trip_id: int, target_user_id: int, req: SetRoleRequest, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.is_owner(trip, user_id):
        raise HTTPException(status_code=403, detail="只有發起人可以變更權限")
    if not await trip_svc.set_member_role(db, trip_id, target_user_id, req.role):
        raise HTTPException(status_code=404)
    return {"message": "權限已更新"}


# ─── Comments (Task 3.2) ────────────────────────────

@router.post("/{trip_id}/items/{item_id}/comments", status_code=201)
async def create_comment(trip_id: int, item_id: int, req: CommentCreate, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.is_member(trip, user_id):
        raise HTTPException(status_code=403)
    comment = comments_mod.add_comment(item_id, user_id, req.text)
    comments_mod.record_edit(trip_id, user_id, "add_comment", f"留言於項目 {item_id}", item_id)
    # Broadcast to other editors (Task 3.1)
    await ws_svc.notify_comment_added(trip_id, item_id, comment.model_dump() if hasattr(comment, 'model_dump') else dict(comment.__dict__))
    return comment


@router.get("/{trip_id}/items/{item_id}/comments")
async def list_comments(trip_id: int, item_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.is_member(trip, user_id):
        raise HTTPException(status_code=403)
    return comments_mod.get_comments(item_id)


# ─── Edit history (Task 3.3) ────────────────────────

@router.get("/{trip_id}/history")
async def get_history(trip_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.is_member(trip, user_id):
        raise HTTPException(status_code=403)
    return comments_mod.get_edit_history(trip_id)


# ─── Finalize (Task 3.4) ────────────────────────────

@router.post("/{trip_id}/finalize")
async def initiate_finalize(trip_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.is_owner(trip, user_id):
        raise HTTPException(status_code=403, detail="只有發起人可以發起定案")
    if trip.status == "finalized":
        raise HTTPException(status_code=400, detail="已經定案了")
    status = await trip_svc.confirm_member(db, trip_id, user_id)
    comments_mod.record_edit(trip_id, user_id, "finalize", "發起定案，等待所有成員確認")
    trip = await trip_svc.get_trip(db, trip_id)
    pending = [m for m in trip.members if not m.confirmed]
    return {"message": "已發起定案", "pending_count": len(pending), "status": trip.status}


@router.post("/{trip_id}/confirm")
async def confirm_trip(trip_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.is_member(trip, user_id):
        raise HTTPException(status_code=403)
    new_status = await trip_svc.confirm_member(db, trip_id, user_id)
    if new_status == "finalized":
        comments_mod.record_edit(trip_id, user_id, "finalize", "全員確認，行程已定案")
        await ws_svc.notify_trip_finalized(trip_id, user_id)
    return {"message": "已確認", "status": new_status}


@router.post("/{trip_id}/unlock")
async def unlock_trip(trip_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await _get_trip_or_404(db, trip_id)
    if not trip_svc.is_owner(trip, user_id):
        raise HTTPException(status_code=403, detail="只有發起人可以解鎖")
    await trip_svc.unlock_trip(db, trip_id)
    comments_mod.record_edit(trip_id, user_id, "unlock", "解鎖行程")
    return {"message": "行程已解鎖", "status": "planning"}


# ─── WebSocket: Real-time collaboration (Task 3.1) ─────

@router.websocket("/{trip_id}/ws")
async def trip_websocket(websocket: WebSocket, trip_id: int, token: str = ""):
    """WebSocket endpoint for real-time trip editing.

    Usage:
        ws://host/api/trips/{trip_id}/ws?token={jwt_token}

    Broadcasts item_added/updated/deleted, comment_added, trip_finalized
    events to all members currently viewing the trip.

    Spec: .req/specs/travel-planner-app/spec.md — US-7
    Task: .req/specs/travel-planner-app/tasks.md — Task 3.1
    """
    # Authenticate via query parameter
    user_id = decode_access_token(token) if token else None
    if user_id is None:
        await websocket.close(code=4401)  # Custom code: unauthorized
        return

    # Verify membership
    async with async_session() as db:
        trip = await trip_svc.get_trip(db, trip_id)
        if not trip or not trip_svc.is_member(trip, user_id):
            await websocket.close(code=4403)  # Custom code: forbidden
            return

    await ws_svc.manager.connect(trip_id, websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "trip_id": trip_id,
            "user_id": user_id,
            "peers": ws_svc.manager.get_connection_count(trip_id),
        })

        # Keep connection alive — relay ping/pong or client messages
        while True:
            data = await websocket.receive_json()
            # Echo back any client-sent events (e.g. cursor position, typing indicator)
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") in ("cursor", "typing"):
                # Broadcast presence indicators to other clients
                data["user_id"] = user_id
                await ws_svc.manager.broadcast(trip_id, data, exclude=websocket)
    except WebSocketDisconnect:
        pass
    finally:
        await ws_svc.manager.disconnect(trip_id, websocket)
