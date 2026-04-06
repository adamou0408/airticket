"""Expense service — database-backed.

Supports recording expenses, budget calculation, and settlement.
"""

import json
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Expense, ItineraryItem, Settlement


async def add_expense(db: AsyncSession, trip_id: int, amount: float, payer_id: int,
                      currency: str, category: str, note: str, split_method: str,
                      split_among: list[int]) -> Expense:
    expense = Expense(
        trip_id=trip_id, amount=amount, currency=currency, category=category,
        payer_id=payer_id, note=note, split_method=split_method,
        split_among=json.dumps(split_among),
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense


async def list_expenses(db: AsyncSession, trip_id: int) -> list[Expense]:
    result = await db.execute(select(Expense).where(Expense.trip_id == trip_id).order_by(Expense.created_at.desc()))
    return list(result.scalars().all())


async def get_budget_summary(db: AsyncSession, trip_id: int, budget: float | None, currency: str) -> dict:
    expenses = await list_expenses(db, trip_id)
    actual_total = sum(e.amount for e in expenses)

    by_category: dict[str, float] = defaultdict(float)
    for e in expenses:
        by_category[e.category] += e.amount

    # Get estimated from itinerary items
    result = await db.execute(select(ItineraryItem).where(ItineraryItem.trip_id == trip_id))
    items = result.scalars().all()
    estimated_total = sum(i.estimated_cost for i in items)

    difference = (budget - (estimated_total + actual_total)) if budget else 0

    return {
        "trip_id": trip_id,
        "estimated_total": estimated_total,
        "budget": budget,
        "over_budget": difference < 0 if budget else False,
        "difference": difference,
        "actual_total": actual_total,
        "by_category": dict(by_category),
        "currency": currency,
    }


async def calculate_settlement(db: AsyncSession, trip_id: int, currency: str) -> dict:
    expenses = await list_expenses(db, trip_id)

    balance: dict[int, float] = defaultdict(float)
    for exp in expenses:
        payer = exp.payer_id
        split_among = json.loads(exp.split_among) if exp.split_among else []
        amount = exp.amount

        if exp.split_method == "equal" and split_among:
            share = amount / len(split_among)
            balance[payer] += amount
            for uid in split_among:
                balance[uid] -= share

    entries = _minimize_transfers(balance, currency)

    # Check settled status
    result = await db.execute(select(Settlement).where(Settlement.trip_id == trip_id))
    settled_map = {(s.from_user, s.to_user): s.settled for s in result.scalars().all()}

    for e in entries:
        e["settled"] = settled_map.get((e["from_user"], e["to_user"]), False)

    return {"trip_id": trip_id, "entries": entries, "currency": currency}


def _minimize_transfers(balance: dict[int, float], currency: str) -> list[dict]:
    creditors = []
    debtors = []
    for uid, bal in balance.items():
        bal = round(bal, 2)
        if bal > 0.01:
            creditors.append([uid, bal])
        elif bal < -0.01:
            debtors.append([uid, -bal])

    creditors.sort(key=lambda x: -x[1])
    debtors.sort(key=lambda x: -x[1])

    entries = []
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debtor_id, debt = debtors[i]
        creditor_id, credit = creditors[j]
        transfer = min(debt, credit)
        if transfer > 0.01:
            entries.append({
                "from_user": debtor_id, "to_user": creditor_id,
                "amount": round(transfer, 2), "currency": currency,
                "settled": False,
            })
        debtors[i][1] -= transfer
        creditors[j][1] -= transfer
        if debtors[i][1] < 0.01:
            i += 1
        if creditors[j][1] < 0.01:
            j += 1
    return entries


async def mark_settled(db: AsyncSession, trip_id: int, from_user: int, to_user: int) -> bool:
    result = await db.execute(
        select(Settlement).where(Settlement.trip_id == trip_id, Settlement.from_user == from_user, Settlement.to_user == to_user)
    )
    s = result.scalar_one_or_none()
    if s:
        s.settled = True
    else:
        db.add(Settlement(trip_id=trip_id, from_user=from_user, to_user=to_user, amount=0, settled=True))
    await db.commit()
    return True
