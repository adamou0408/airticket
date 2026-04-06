"""SQLAlchemy ORM models — all database tables.

Replaces in-memory stores with persistent PostgreSQL storage.
Also supports SQLite for development/testing.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ─── Auth ────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ─── Trips ───────────────────────────────────────────

class TripStatusEnum(str, enum.Enum):
    planning = "planning"
    finalized = "finalized"


class MemberRoleEnum(str, enum.Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"


class ItemTypeEnum(str, enum.Enum):
    attraction = "attraction"
    restaurant = "restaurant"
    transport = "transport"
    accommodation = "accommodation"
    other = "other"


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    destination: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    end_date: Mapped[str] = mapped_column(String(10), nullable=False)
    budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="TWD")
    status: Mapped[str] = mapped_column(String(20), default="planning")
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)
    share_token: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    members: Mapped[list["TripMember"]] = relationship(back_populates="trip", cascade="all, delete-orphan")
    items: Mapped[list["ItineraryItem"]] = relationship(back_populates="trip", cascade="all, delete-orphan")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="trip", cascade="all, delete-orphan")


class TripMember(Base):
    __tablename__ = "trip_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="editor")
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    trip: Mapped["Trip"] = relationship(back_populates="members")


class ItineraryItem(Base):
    __tablename__ = "itinerary_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    type: Mapped[str] = mapped_column(String(20), default="other")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    time: Mapped[str] = mapped_column(String(10), default="")
    location: Mapped[str] = mapped_column(String(200), default="")
    note: Mapped[str] = mapped_column(Text, default="")
    estimated_cost: Mapped[float] = mapped_column(Float, default=0)
    created_by: Mapped[int] = mapped_column(Integer, nullable=False)

    trip: Mapped["Trip"] = relationship(back_populates="items")


# ─── Expenses ────────────────────────────────────────

class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="TWD")
    category: Mapped[str] = mapped_column(String(20), default="other")
    payer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str] = mapped_column(Text, default="")
    receipt_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    split_method: Mapped[str] = mapped_column(String(20), default="equal")
    split_among: Mapped[str] = mapped_column(Text, default="")  # JSON array of user IDs
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    trip: Mapped["Trip"] = relationship(back_populates="expenses")


# ─── Comments & History ──────────────────────────────

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EditHistory(Base):
    __tablename__ = "edit_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(Integer, nullable=False)
    item_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(Integer, nullable=False)
    from_user: Mapped[int] = mapped_column(Integer, nullable=False)
    to_user: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="TWD")
    settled: Mapped[bool] = mapped_column(Boolean, default=False)


# ─── Crawl Schedules ────────────────────────────────

class CrawlSchedule(Base):
    __tablename__ = "crawl_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    origin: Mapped[str] = mapped_column(String(10), nullable=False)
    destination: Mapped[str] = mapped_column(String(10), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_result_count: Mapped[int] = mapped_column(Integer, default=0)
    target_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    alert_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    lowest_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    origin: Mapped[str] = mapped_column(String(10), nullable=False)
    destination: Mapped[str] = mapped_column(String(10), nullable=False)
    lowest_price: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
