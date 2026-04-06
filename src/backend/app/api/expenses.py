"""Expense API endpoints — database-backed."""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user_id
from app.core.database import get_db
from app.expenses.models import CreateExpenseRequest
from app.expenses import service as exp_svc
from app.trips import service as trip_svc

router = APIRouter(prefix="/trips/{trip_id}/expenses", tags=["expenses"])


def _expense_to_dict(e):
    return {
        "id": e.id, "trip_id": e.trip_id, "amount": e.amount,
        "currency": e.currency, "category": e.category,
        "payer_id": e.payer_id, "note": e.note,
        "receipt_url": e.receipt_url, "split_method": e.split_method,
        "split_among": json.loads(e.split_among) if e.split_among else [],
        "created_at": e.created_at.isoformat() if e.created_at else "",
    }


@router.post("", status_code=201)
async def create_expense(trip_id: int, req: CreateExpenseRequest,
                         user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await trip_svc.get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="旅遊計畫不存在")
    if not trip_svc.is_member(trip, user_id):
        raise HTTPException(status_code=403, detail="你不是這個計畫的成員")
    all_members = [m.user_id for m in trip.members]
    split_among = req.split_among if req.split_among else all_members
    expense = await exp_svc.add_expense(db, trip_id, req.amount, req.payer_id, req.currency, req.category, req.note, req.split_method, split_among)
    return _expense_to_dict(expense)


@router.get("")
async def get_expenses(trip_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await trip_svc.get_trip(db, trip_id)
    if not trip or not trip_svc.is_member(trip, user_id):
        raise HTTPException(status_code=403)
    expenses = await exp_svc.list_expenses(db, trip_id)
    return [_expense_to_dict(e) for e in expenses]


@router.get("/budget")
async def get_budget(trip_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await trip_svc.get_trip(db, trip_id)
    if not trip or not trip_svc.is_member(trip, user_id):
        raise HTTPException(status_code=403)
    return await exp_svc.get_budget_summary(db, trip_id, trip.budget, trip.currency)


@router.get("/settlement")
async def get_settlement(trip_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await trip_svc.get_trip(db, trip_id)
    if not trip or not trip_svc.is_member(trip, user_id):
        raise HTTPException(status_code=403)
    return await exp_svc.calculate_settlement(db, trip_id, trip.currency)


@router.put("/settlement/settle")
async def settle_payment(trip_id: int, from_user: int, to_user: int,
                         user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    trip = await trip_svc.get_trip(db, trip_id)
    if not trip or not trip_svc.is_member(trip, user_id):
        raise HTTPException(status_code=403)
    await exp_svc.mark_settled(db, trip_id, from_user, to_user)
    return {"message": "已標記為已結清"}
