"""Share and export service — database-backed."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.expenses import service as exp_svc
from app.trips import service as trip_svc


async def export_trip_text(db: AsyncSession, trip_id: int) -> str | None:
    trip = await trip_svc.get_trip(db, trip_id)
    if not trip:
        return None

    lines = []
    lines.append(f"✈️ {trip.name}")
    lines.append(f"📍 目的地：{trip.destination}")
    lines.append(f"📅 {trip.start_date} ~ {trip.end_date}")
    if trip.budget:
        lines.append(f"💰 預算：{trip.currency} {trip.budget:,.0f}")
    lines.append(f"👥 成員：{len(trip.members)} 人")
    lines.append(f"📋 狀態：{trip.status}")
    lines.append("")

    days: dict[int, list] = {}
    for item in trip.items:
        days.setdefault(item.day_number, []).append(item)

    for day_num in sorted(days.keys()):
        lines.append(f"--- Day {day_num} ---")
        for item in sorted(days[day_num], key=lambda x: x.order):
            time_str = f" {item.time}" if item.time else ""
            cost_str = f" (${item.estimated_cost:,.0f})" if item.estimated_cost else ""
            lines.append(f"  {item.type}{time_str} | {item.name}{cost_str}")
            if item.location:
                lines.append(f"    📍 {item.location}")
            if item.note:
                lines.append(f"    📝 {item.note}")
        lines.append("")

    return "\n".join(lines)


async def export_trip_json(db: AsyncSession, trip_id: int) -> dict | None:
    trip = await trip_svc.get_trip(db, trip_id)
    if not trip:
        return None
    # Build a dict manually since we're using ORM models now
    return {
        "id": trip.id, "name": trip.name, "destination": trip.destination,
        "start_date": trip.start_date, "end_date": trip.end_date,
        "budget": trip.budget, "currency": trip.currency,
        "status": trip.status, "owner_id": trip.owner_id,
        "members": [{"user_id": m.user_id, "role": m.role, "confirmed": m.confirmed} for m in trip.members],
        "items": sorted([{
            "id": i.id, "day_number": i.day_number, "order": i.order,
            "type": i.type, "name": i.name, "time": i.time,
            "location": i.location, "note": i.note,
            "estimated_cost": i.estimated_cost,
        } for i in trip.items], key=lambda x: (x["day_number"], x["order"])),
    }


async def get_shared_trip(db: AsyncSession, share_token: str) -> dict | None:
    trip = await trip_svc.get_trip_by_token(db, share_token)
    if not trip:
        return None
    return await export_trip_json(db, trip.id)


async def export_settlement_text(db: AsyncSession, trip_id: int) -> str | None:
    trip = await trip_svc.get_trip(db, trip_id)
    if not trip:
        return None

    currency = trip.currency
    report = await exp_svc.calculate_settlement(db, trip_id, currency)
    expenses = await exp_svc.list_expenses(db, trip_id)
    total = sum(e.amount for e in expenses)

    lines = []
    lines.append(f"💰 旅遊拆帳結算 — {trip.name}")
    lines.append(f"總花費：{currency} {total:,.0f}")
    lines.append(f"筆數：{len(expenses)} 筆")
    lines.append("")

    if not report["entries"]:
        lines.append("✅ 大家都結清了，不需要轉帳！")
    else:
        lines.append("📋 轉帳清單：")
        for entry in report["entries"]:
            status = "✅ 已結清" if entry["settled"] else "⏳ 待轉帳"
            lines.append(f"  用戶 {entry['from_user']} → 用戶 {entry['to_user']}：{currency} {entry['amount']:,.0f} {status}")

    return "\n".join(lines)
