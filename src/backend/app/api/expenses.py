"""Expense API endpoints.

Spec: specs/travel-planner-app/spec.md — US-9, US-10, US-11
Task: 4.2 — Quick expense API
Task: 4.3 — Budget estimation API
Task: 4.4 — Settlement API
"""

from fastapi import APIRouter, Depends, HTTPException

from app.auth.deps import get_current_user_id
from app.expenses.models import (
    BudgetSummary,
    CreateExpenseRequest,
    Expense,
    SettlementReport,
)
from app.expenses.service import (
    add_expense,
    calculate_settlement,
    get_budget_summary,
    list_expenses,
    mark_settled,
)
from app.trips.service import get_trip, is_member

router = APIRouter(prefix="/trips/{trip_id}/expenses", tags=["expenses"])


def _get_trip_or_404(trip_id: int):
    trip = get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="旅遊計畫不存在")
    return trip


@router.post("", response_model=Expense, status_code=201)
async def create_expense(
    trip_id: int,
    req: CreateExpenseRequest,
    user_id: int = Depends(get_current_user_id),
):
    """Quick expense recording — only amount + payer required."""
    trip = _get_trip_or_404(trip_id)
    if not is_member(trip_id, user_id):
        raise HTTPException(status_code=403, detail="你不是這個計畫的成員")
    all_members = list(trip["members"].keys())
    return add_expense(trip_id, req, all_members)


@router.get("", response_model=list[Expense])
async def get_expenses(
    trip_id: int,
    user_id: int = Depends(get_current_user_id),
):
    """List all expenses for a trip."""
    if not is_member(trip_id, user_id):
        raise HTTPException(status_code=403)
    return list_expenses(trip_id)


@router.get("/budget", response_model=BudgetSummary)
async def get_budget(
    trip_id: int,
    user_id: int = Depends(get_current_user_id),
):
    """Get budget summary — estimated vs actual, by category."""
    trip = _get_trip_or_404(trip_id)
    if not is_member(trip_id, user_id):
        raise HTTPException(status_code=403)

    # Calculate estimated cost from itinerary items
    from app.trips.service import _items
    estimated = sum(
        i["estimated_cost"] for i in _items.values() if i["trip_id"] == trip_id
    )

    return get_budget_summary(trip_id, trip.get("budget"), estimated, trip.get("currency", "TWD"))


@router.get("/settlement", response_model=SettlementReport)
async def get_settlement(
    trip_id: int,
    user_id: int = Depends(get_current_user_id),
):
    """Calculate settlement — who owes whom, minimized transfers."""
    trip = _get_trip_or_404(trip_id)
    if not is_member(trip_id, user_id):
        raise HTTPException(status_code=403)
    return calculate_settlement(trip_id, trip.get("currency", "TWD"))


@router.put("/settlement/settle")
async def settle_payment(
    trip_id: int,
    from_user: int,
    to_user: int,
    user_id: int = Depends(get_current_user_id),
):
    """Mark a settlement entry as paid."""
    if not is_member(trip_id, user_id):
        raise HTTPException(status_code=403)
    mark_settled(trip_id, from_user, to_user)
    return {"message": "已標記為已結清"}
