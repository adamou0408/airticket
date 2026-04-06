"""Crawl schedule service — manage user routes + daily crawl engine.

D.1: Daily scheduled crawl engine
D.2: User custom schedule API
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import CrawlSchedule
from app.flights.crawler_router import router as crawler_router

logger = logging.getLogger(__name__)

# Default popular routes (always crawled)
DEFAULT_ROUTES = [
    ("TPE", "NRT"), ("TPE", "KIX"), ("TPE", "ICN"),
    ("TPE", "BKK"), ("TPE", "SIN"), ("TPE", "HKG"),
    ("TPE", "HND"), ("TPE", "OKA"), ("TPE", "FUK"),
    ("TPE", "CDG"), ("TPE", "LAX"),
]


# ─── CRUD ────────────────────────────────────────────

async def add_schedule(db: AsyncSession, user_id: int, origin: str, destination: str) -> CrawlSchedule:
    """Add a user's custom crawl schedule. Dedup: skip if same route exists."""
    existing = await db.execute(
        select(CrawlSchedule).where(
            CrawlSchedule.user_id == user_id,
            CrawlSchedule.origin == origin,
            CrawlSchedule.destination == destination,
        )
    )
    found = existing.scalar_one_or_none()
    if found:
        found.enabled = True
        await db.commit()
        await db.refresh(found)
        return found

    schedule = CrawlSchedule(user_id=user_id, origin=origin, destination=destination)
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def list_user_schedules(db: AsyncSession, user_id: int) -> list[CrawlSchedule]:
    result = await db.execute(
        select(CrawlSchedule).where(CrawlSchedule.user_id == user_id).order_by(CrawlSchedule.created_at.desc())
    )
    return list(result.scalars().all())


async def set_target_price(db: AsyncSession, schedule_id: int, user_id: int, target_price: float) -> CrawlSchedule | None:
    """Set target price for price alert (US-21)."""
    result = await db.execute(
        select(CrawlSchedule).where(CrawlSchedule.id == schedule_id, CrawlSchedule.user_id == user_id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        return None
    schedule.target_price = target_price
    schedule.alert_triggered = False  # Reset alert when target changes
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def delete_schedule(db: AsyncSession, schedule_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(CrawlSchedule).where(CrawlSchedule.id == schedule_id, CrawlSchedule.user_id == user_id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        return False
    await db.delete(schedule)
    await db.commit()
    return True


async def toggle_schedule(db: AsyncSession, schedule_id: int, user_id: int) -> CrawlSchedule | None:
    result = await db.execute(
        select(CrawlSchedule).where(CrawlSchedule.id == schedule_id, CrawlSchedule.user_id == user_id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        return None
    schedule.enabled = not schedule.enabled
    await db.commit()
    await db.refresh(schedule)
    return schedule


# ─── Crawl Engine ────────────────────────────────────

async def get_all_routes_to_crawl(db: AsyncSession) -> list[tuple[str, str]]:
    """Get all unique routes to crawl: default + all users' enabled schedules."""
    routes = set(DEFAULT_ROUTES)

    result = await db.execute(
        select(CrawlSchedule).where(CrawlSchedule.enabled == True)
    )
    for s in result.scalars().all():
        routes.add((s.origin, s.destination))

    return list(routes)


async def run_daily_crawl(db: AsyncSession) -> dict:
    """Execute the daily crawl for all routes.

    Returns a summary of results.
    """
    routes = await get_all_routes_to_crawl(db)
    logger.info(f"Daily crawl: {len(routes)} routes to crawl")

    # Crawl dates: today + next 30 days (sample a few dates)
    today = date.today()
    sample_dates = [
        today + timedelta(days=7),
        today + timedelta(days=14),
        today + timedelta(days=30),
    ]

    summary = {"total_routes": len(routes), "crawled": 0, "results": 0, "errors": 0}

    for origin, dest in routes:
        for travel_date in sample_dates:
            try:
                flights, sources = await crawler_router.search(origin, dest, travel_date, 1)
                real_count = sum(1 for f in flights if f.source != "simulated")
                summary["crawled"] += 1
                summary["results"] += real_count

                # Update schedule last_crawled for user schedules
                await _update_schedule_status(db, origin, dest, real_count)

            except Exception as e:
                logger.error(f"Crawl failed for {origin}→{dest}: {e}")
                summary["errors"] += 1

    logger.info(f"Daily crawl complete: {summary}")
    return summary


async def _update_schedule_status(db: AsyncSession, origin: str, dest: str, result_count: int):
    """Update last_crawled_at for all matching schedules."""
    result = await db.execute(
        select(CrawlSchedule).where(
            CrawlSchedule.origin == origin,
            CrawlSchedule.destination == dest,
            CrawlSchedule.enabled == True,
        )
    )
    now = datetime.now(timezone.utc)
    for schedule in result.scalars().all():
        schedule.last_crawled_at = now
        schedule.last_result_count = result_count
    await db.commit()


async def run_crawl_for_route(origin: str, dest: str, travel_date: date) -> dict:
    """Crawl a single route immediately. Returns results summary."""
    flights, sources = await crawler_router.search(origin, dest, travel_date, 1)
    return {
        "origin": origin,
        "destination": dest,
        "date": travel_date.isoformat(),
        "total_flights": len(flights),
        "real_flights": sum(1 for f in flights if f.source != "simulated"),
        "sources": sources,
    }
