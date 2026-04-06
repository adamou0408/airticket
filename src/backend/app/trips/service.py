"""Trip service — database-backed."""

import json
import secrets

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import Trip, TripMember, ItineraryItem


async def create_trip(db: AsyncSession, name: str, destination: str, start_date, end_date, budget, currency: str, owner_id: int) -> Trip:
    token = secrets.token_urlsafe(16)
    trip = Trip(
        name=name, destination=destination,
        start_date=str(start_date), end_date=str(end_date),
        budget=budget, currency=currency,
        owner_id=owner_id, share_token=token,
    )
    db.add(trip)
    await db.flush()
    member = TripMember(trip_id=trip.id, user_id=owner_id, role="owner", confirmed=True)
    db.add(member)
    await db.commit()
    await db.refresh(trip, ["members"])
    return trip


async def get_trip(db: AsyncSession, trip_id: int) -> Trip | None:
    result = await db.execute(
        select(Trip).options(selectinload(Trip.members), selectinload(Trip.items)).where(Trip.id == trip_id)
    )
    return result.scalar_one_or_none()


async def get_trip_by_token(db: AsyncSession, token: str) -> Trip | None:
    result = await db.execute(
        select(Trip).options(selectinload(Trip.members), selectinload(Trip.items)).where(Trip.share_token == token)
    )
    return result.scalar_one_or_none()


async def list_user_trips(db: AsyncSession, user_id: int) -> list[Trip]:
    result = await db.execute(
        select(Trip).join(TripMember).where(TripMember.user_id == user_id).options(selectinload(Trip.members))
    )
    return list(result.scalars().unique().all())


async def update_trip(db: AsyncSession, trip_id: int, **kwargs) -> Trip | None:
    trip = await get_trip(db, trip_id)
    if not trip:
        return None
    for k, v in kwargs.items():
        if v is not None and hasattr(trip, k):
            setattr(trip, k, str(v) if k in ("start_date", "end_date") else v)
    await db.commit()
    await db.refresh(trip)
    return trip


async def delete_trip(db: AsyncSession, trip_id: int) -> bool:
    trip = await get_trip(db, trip_id)
    if not trip:
        return False
    await db.delete(trip)
    await db.commit()
    return True


async def add_item(db: AsyncSession, trip_id: int, day_number: int, type_: str, name: str,
                   time: str, location: str, note: str, estimated_cost: float, user_id: int) -> ItineraryItem:
    # Get next order
    result = await db.execute(
        select(ItineraryItem).where(ItineraryItem.trip_id == trip_id, ItineraryItem.day_number == day_number)
    )
    existing = result.scalars().all()
    order = len(existing) + 1

    item = ItineraryItem(
        trip_id=trip_id, day_number=day_number, order=order,
        type=type_, name=name, time=time, location=location,
        note=note, estimated_cost=estimated_cost, created_by=user_id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_item(db: AsyncSession, item_id: int, **kwargs) -> ItineraryItem | None:
    result = await db.execute(select(ItineraryItem).where(ItineraryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return None
    for k, v in kwargs.items():
        if v is not None and hasattr(item, k):
            setattr(item, k, v)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item_id: int) -> bool:
    result = await db.execute(select(ItineraryItem).where(ItineraryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return False
    await db.delete(item)
    await db.commit()
    return True


async def reorder_items(db: AsyncSession, trip_id: int, item_ids: list[int]):
    for order, iid in enumerate(item_ids, 1):
        result = await db.execute(select(ItineraryItem).where(ItineraryItem.id == iid, ItineraryItem.trip_id == trip_id))
        item = result.scalar_one_or_none()
        if item:
            item.order = order
    await db.commit()


async def join_trip(db: AsyncSession, trip_id: int, user_id: int, role: str = "editor") -> bool:
    # Check not already member
    result = await db.execute(
        select(TripMember).where(TripMember.trip_id == trip_id, TripMember.user_id == user_id)
    )
    if result.scalar_one_or_none():
        return True  # Already a member
    member = TripMember(trip_id=trip_id, user_id=user_id, role=role, confirmed=False)
    db.add(member)
    await db.commit()
    return True


async def set_member_role(db: AsyncSession, trip_id: int, user_id: int, role: str) -> bool:
    result = await db.execute(
        select(TripMember).where(TripMember.trip_id == trip_id, TripMember.user_id == user_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        return False
    member.role = role
    await db.commit()
    return True


def is_member(trip: Trip, user_id: int) -> bool:
    return any(m.user_id == user_id for m in trip.members)


def is_owner(trip: Trip, user_id: int) -> bool:
    return trip.owner_id == user_id


def can_edit(trip: Trip, user_id: int) -> bool:
    for m in trip.members:
        if m.user_id == user_id and m.role in ("owner", "editor"):
            return True
    return False


async def confirm_member(db: AsyncSession, trip_id: int, user_id: int) -> str:
    """Confirm a member. Returns trip status after confirmation."""
    trip = await get_trip(db, trip_id)
    if not trip:
        return "unknown"
    for m in trip.members:
        if m.user_id == user_id:
            m.confirmed = True
    if all(m.confirmed for m in trip.members):
        trip.status = "finalized"
    await db.commit()
    return trip.status


async def unlock_trip(db: AsyncSession, trip_id: int) -> bool:
    trip = await get_trip(db, trip_id)
    if not trip:
        return False
    trip.status = "planning"
    for m in trip.members:
        m.confirmed = False
    await db.commit()
    return True
