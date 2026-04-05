"""Expense data models.

Spec: specs/travel-planner-app/spec.md — US-9, US-10, US-11
Task: 4.1 — Expense data models
"""

from enum import Enum

from pydantic import BaseModel, Field


class ExpenseCategory(str, Enum):
    transport = "transport"          # 交通
    accommodation = "accommodation"  # 住宿
    food = "food"                    # 餐飲
    ticket = "ticket"               # 門票
    shopping = "shopping"           # 購物
    other = "other"


class SplitMethod(str, Enum):
    equal = "equal"          # 均分
    ratio = "ratio"          # 按比例
    custom = "custom"        # 自訂金額


class CreateExpenseRequest(BaseModel):
    """Quick expense creation — only amount + payer required (CONFLICT-003 decision)."""
    amount: float = Field(..., gt=0)
    payer_id: int
    currency: str = "TWD"
    category: ExpenseCategory = ExpenseCategory.other
    note: str = ""
    split_among: list[int] | None = Field(None, description="User IDs to split among; None = all members")
    split_method: SplitMethod = SplitMethod.equal


class Expense(BaseModel):
    id: int
    trip_id: int
    amount: float
    currency: str
    category: ExpenseCategory
    payer_id: int
    note: str
    receipt_url: str | None = None
    split_method: SplitMethod
    split_among: list[int]
    created_at: str


class BudgetSummary(BaseModel):
    trip_id: int
    estimated_total: float
    budget: float | None
    over_budget: bool
    difference: float  # positive = under budget, negative = over
    actual_total: float
    by_category: dict[str, float]
    currency: str


class SettlementEntry(BaseModel):
    from_user: int
    to_user: int
    amount: float
    currency: str
    settled: bool = False


class SettlementReport(BaseModel):
    trip_id: int
    entries: list[SettlementEntry]
    currency: str
