"""Share and export API — database-backed."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user_id
from app.core.database import get_db
from app.trips import service as trip_svc
from app.trips.share import export_settlement_text, export_trip_json, export_trip_text, get_shared_trip

router = APIRouter(tags=["share"])


@router.get("/trips/{trip_id}/export/text", response_class=PlainTextResponse)
async def export_text(trip_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await trip_svc.get_trip(db, trip_id)
    if not trip or not trip_svc.is_member(trip, user_id):
        raise HTTPException(status_code=403)
    result = await export_trip_text(db, trip_id)
    if not result:
        raise HTTPException(status_code=404)
    return result


@router.get("/trips/{trip_id}/export/json")
async def export_json(trip_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await trip_svc.get_trip(db, trip_id)
    if not trip or not trip_svc.is_member(trip, user_id):
        raise HTTPException(status_code=403)
    result = await export_trip_json(db, trip_id)
    if not result:
        raise HTTPException(status_code=404)
    return result


@router.get("/share/{share_token}")
async def view_shared_trip(share_token: str, db: AsyncSession = Depends(get_db)):
    result = await get_shared_trip(db, share_token)
    if not result:
        raise HTTPException(status_code=404, detail="分享連結無效或已過期")
    return result


@router.get("/trips/{trip_id}/settlement/export/text", response_class=PlainTextResponse)
async def export_settlement(trip_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await trip_svc.get_trip(db, trip_id)
    if not trip or not trip_svc.is_member(trip, user_id):
        raise HTTPException(status_code=403)
    result = await export_settlement_text(db, trip_id)
    if not result:
        raise HTTPException(status_code=404)
    return result
