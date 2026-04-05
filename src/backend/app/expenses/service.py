"""Expense service — record expenses, calculate budget, settle accounts.

Spec: specs/travel-planner-app/spec.md — US-9, US-10, US-11
Task: 4.2 — Quick expense recording
Task: 4.3 — Budget estimation
Task: 4.4 — Split/settlement engine
"""

from collections import defaultdict
from datetime import datetime, timezone

from app.expenses.models import (
    BudgetSummary,
    CreateExpenseRequest,
    Expense,
    SettlementEntry,
    SettlementReport,
    SplitMethod,
)

# In-memory store
_expenses: dict[int, dict] = {}  # expense_id -> expense data
_settled: dict[str, bool] = {}  # "from_user:to_user:trip_id" -> settled
_next_expense_id = 1


def _reset():
    global _next_expense_id
    _expenses.clear()
    _settled.clear()
    _next_expense_id = 1


def add_expense(trip_id: int, req: CreateExpenseRequest, all_member_ids: list[int]) -> Expense:
    global _next_expense_id
    split_among = req.split_among if req.split_among else all_member_ids
    now = datetime.now(timezone.utc).isoformat()

    expense = {
        "id": _next_expense_id,
        "trip_id": trip_id,
        "amount": req.amount,
        "currency": req.currency,
        "category": req.category,
        "payer_id": req.payer_id,
        "note": req.note,
        "receipt_url": None,
        "split_method": req.split_method,
        "split_among": split_among,
        "created_at": now,
    }
    _expenses[_next_expense_id] = expense
    _next_expense_id += 1
    return Expense(**expense)


def list_expenses(trip_id: int) -> list[Expense]:
    return [Expense(**e) for e in _expenses.values() if e["trip_id"] == trip_id]


def get_budget_summary(trip_id: int, budget: float | None, estimated_from_items: float, currency: str) -> BudgetSummary:
    """Calculate budget summary from actual expenses + item estimates."""
    expenses = [e for e in _expenses.values() if e["trip_id"] == trip_id]
    actual_total = sum(e["amount"] for e in expenses)

    by_category: dict[str, float] = defaultdict(float)
    for e in expenses:
        by_category[e["category"]] += e["amount"]

    difference = (budget - (estimated_from_items + actual_total)) if budget else 0

    return BudgetSummary(
        trip_id=trip_id,
        estimated_total=estimated_from_items,
        budget=budget,
        over_budget=difference < 0 if budget else False,
        difference=difference,
        actual_total=actual_total,
        by_category=dict(by_category),
        currency=currency,
    )


def calculate_settlement(trip_id: int, currency: str) -> SettlementReport:
    """Calculate who owes whom using the minimum transfer algorithm.

    Algorithm:
    1. For each expense, calculate each person's share.
    2. Sum up net balance per person (paid - owed).
    3. Use greedy matching to minimize number of transfers.
    """
    expenses = [e for e in _expenses.values() if e["trip_id"] == trip_id]

    # Net balance: positive = others owe you, negative = you owe others
    balance: dict[int, float] = defaultdict(float)

    for exp in expenses:
        payer = exp["payer_id"]
        split_among = exp["split_among"]
        method = exp["split_method"]
        amount = exp["amount"]

        if method == SplitMethod.equal:
            share = amount / len(split_among)
            balance[payer] += amount  # payer paid
            for uid in split_among:
                balance[uid] -= share  # each person owes their share

    # Simplify: minimum transfers using greedy
    entries = _minimize_transfers(balance, trip_id, currency)

    return SettlementReport(
        trip_id=trip_id,
        entries=entries,
        currency=currency,
    )


def _minimize_transfers(balance: dict[int, float], trip_id: int, currency: str) -> list[SettlementEntry]:
    """Greedy algorithm to minimize number of transfers."""
    # Round to avoid floating point issues
    creditors = []  # (user_id, amount_owed_to_them)
    debtors = []    # (user_id, amount_they_owe)

    for uid, bal in balance.items():
        bal = round(bal, 2)
        if bal > 0.01:
            creditors.append([uid, bal])
        elif bal < -0.01:
            debtors.append([uid, -bal])

    # Sort for deterministic results
    creditors.sort(key=lambda x: -x[1])
    debtors.sort(key=lambda x: -x[1])

    entries = []
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debtor_id, debt = debtors[i]
        creditor_id, credit = creditors[j]
        transfer = min(debt, credit)

        if transfer > 0.01:
            settle_key = f"{debtor_id}:{creditor_id}:{trip_id}"
            entries.append(SettlementEntry(
                from_user=debtor_id,
                to_user=creditor_id,
                amount=round(transfer, 2),
                currency=currency,
                settled=_settled.get(settle_key, False),
            ))

        debtors[i][1] -= transfer
        creditors[j][1] -= transfer

        if debtors[i][1] < 0.01:
            i += 1
        if creditors[j][1] < 0.01:
            j += 1

    return entries


def mark_settled(trip_id: int, from_user: int, to_user: int) -> bool:
    key = f"{from_user}:{to_user}:{trip_id}"
    _settled[key] = True
    return True
