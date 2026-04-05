"""Trip data models — in-memory for MVP.

Spec: specs/travel-planner-app/spec.md — US-3, US-4, US-5, US-6, US-7
Task: 2.2 — Data models for trips
Task: 2.3 — Trip CRUD API
Task: 2.4 — Invite and permission API
"""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class TripStatus(str, Enum):
    planning = "planning"
    finalized = "finalized"


class MemberRole(str, Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"


class ItemType(str, Enum):
    attraction = "attraction"    # 景點
    restaurant = "restaurant"    # 餐廳
    transport = "transport"      # 交通
    accommodation = "accommodation"  # 住宿
    other = "other"


# --- Request/Response schemas ---

class CreateTripRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    destination: str = Field(..., min_length=1)
    start_date: date
    end_date: date
    budget: float | None = None
    currency: str = "TWD"


class TripSummary(BaseModel):
    id: int
    name: str
    destination: str
    start_date: date
    end_date: date
    budget: float | None
    currency: str
    status: TripStatus
    owner_id: int
    member_count: int
    share_token: str


class TripMember(BaseModel):
    user_id: int
    name: str
    role: MemberRole
    confirmed: bool = False


class CreateItemRequest(BaseModel):
    day_number: int = Field(..., ge=1)
    type: ItemType = ItemType.other
    name: str = Field(..., min_length=1)
    time: str = ""
    location: str = ""
    note: str = ""
    estimated_cost: float = 0


class ItineraryItem(BaseModel):
    id: int
    day_number: int
    order: int
    type: ItemType
    name: str
    time: str
    location: str
    note: str
    estimated_cost: float
    created_by: int


class ReorderRequest(BaseModel):
    item_ids: list[int] = Field(..., description="Ordered list of item IDs")


class TripDetail(BaseModel):
    id: int
    name: str
    destination: str
    start_date: date
    end_date: date
    budget: float | None
    currency: str
    status: TripStatus
    owner_id: int
    share_token: str
    members: list[TripMember]
    items: list[ItineraryItem]


class InviteResponse(BaseModel):
    invite_link: str
    share_token: str


class SetRoleRequest(BaseModel):
    role: MemberRole
