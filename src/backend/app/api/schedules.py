"""Crawl schedule API — user custom routes + manual trigger.

D.2: User custom schedule API
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user_id
from app.core.database import get_db
from app.scheduler import service as sched_svc

router = APIRouter(prefix="/crawl-schedules", tags=["schedules"])


class CreateScheduleRequest(BaseModel):
    origin: str = Field(..., min_length=3, max_length=4)
    destination: str = Field(..., min_length=3, max_length=4)


class SetTargetPriceRequest(BaseModel):
    target_price: float = Field(..., gt=0)


class ScheduleResponse(BaseModel):
    id: int
    origin: str
    destination: str
    enabled: bool
    last_crawled_at: str | None
    last_result_count: int
    target_price: float | None
    alert_triggered: bool
    lowest_price: float | None
    created_at: str

    @classmethod
    def from_model(cls, s):
        return cls(
            id=s.id, origin=s.origin, destination=s.destination,
            enabled=s.enabled,
            last_crawled_at=s.last_crawled_at.isoformat() if s.last_crawled_at else None,
            last_result_count=s.last_result_count,
            target_price=getattr(s, 'target_price', None),
            alert_triggered=getattr(s, 'alert_triggered', False),
            lowest_price=getattr(s, 'lowest_price', None),
            created_at=s.created_at.isoformat() if s.created_at else "",
        )


@router.post("", status_code=201)
async def create_schedule(
    req: CreateScheduleRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Add a route to daily crawl schedule."""
    s = await sched_svc.add_schedule(db, user_id, req.origin.upper(), req.destination.upper())
    return ScheduleResponse.from_model(s)


@router.get("")
async def list_schedules(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List my crawl schedules."""
    schedules = await sched_svc.list_user_schedules(db, user_id)
    return [ScheduleResponse.from_model(s) for s in schedules]


@router.delete("/{schedule_id}", status_code=204)
async def remove_schedule(
    schedule_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Remove a route from daily crawl schedule."""
    if not await sched_svc.delete_schedule(db, schedule_id, user_id):
        raise HTTPException(status_code=404, detail="排程不存在")


@router.put("/{schedule_id}/toggle")
async def toggle(
    schedule_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Toggle schedule enabled/disabled."""
    s = await sched_svc.toggle_schedule(db, schedule_id, user_id)
    if not s:
        raise HTTPException(status_code=404)
    return ScheduleResponse.from_model(s)


@router.post("/crawl-now")
async def manual_crawl(
    req: CreateScheduleRequest,
    user_id: int = Depends(get_current_user_id),
):
    """Manually trigger a crawl for a specific route right now."""
    from datetime import timedelta
    travel_date = date.today() + timedelta(days=14)
    result = await sched_svc.run_crawl_for_route(req.origin.upper(), req.destination.upper(), travel_date)
    return result


@router.put("/{schedule_id}/target")
async def set_target_price(
    schedule_id: int,
    req: SetTargetPriceRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Set target price for a tracked route (US-21)."""
    s = await sched_svc.set_target_price(db, schedule_id, user_id, req.target_price)
    if not s:
        raise HTTPException(status_code=404)
    return ScheduleResponse.from_model(s)


@router.get("/default-routes")
async def default_routes():
    """List the default popular routes that are always crawled."""
    return [{"origin": o, "destination": d} for o, d in sched_svc.DEFAULT_ROUTES]
