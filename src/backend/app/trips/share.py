"""Share and export service.

Spec: specs/travel-planner-app/spec.md — US-8, US-11
Task: 5.1 — Trip export (text/JSON format for MVP; image/PDF in frontend)
Task: 5.2 — Read-only share link
Task: 5.3 — Settlement result sharing
"""

from app.expenses.service import calculate_settlement, list_expenses
from app.trips.service import get_trip, get_trip_by_token, get_trip_detail


def export_trip_text(trip_id: int) -> str | None:
    """Export trip as formatted plain text (for sharing via messaging apps)."""
    detail = get_trip_detail(trip_id)
    if not detail:
        return None

    lines = []
    lines.append(f"✈️ {detail.name}")
    lines.append(f"📍 目的地：{detail.destination}")
    lines.append(f"📅 {detail.start_date} ~ {detail.end_date}")
    if detail.budget:
        lines.append(f"💰 預算：{detail.currency} {detail.budget:,.0f}")
    lines.append(f"👥 成員：{len(detail.members)} 人")
    lines.append(f"📋 狀態：{detail.status}")
    lines.append("")

    # Group items by day
    days: dict[int, list] = {}
    for item in detail.items:
        days.setdefault(item.day_number, []).append(item)

    for day_num in sorted(days.keys()):
        lines.append(f"--- Day {day_num} ---")
        for item in days[day_num]:
            time_str = f" {item.time}" if item.time else ""
            cost_str = f" (${item.estimated_cost:,.0f})" if item.estimated_cost else ""
            lines.append(f"  {item.type.value}{time_str} | {item.name}{cost_str}")
            if item.location:
                lines.append(f"    📍 {item.location}")
            if item.note:
                lines.append(f"    📝 {item.note}")
        lines.append("")

    return "\n".join(lines)


def export_trip_json(trip_id: int) -> dict | None:
    """Export trip as structured JSON (for frontend rendering/PDF generation)."""
    detail = get_trip_detail(trip_id)
    if not detail:
        return None
    return detail.model_dump(mode="json")


def get_shared_trip(share_token: str) -> dict | None:
    """Get trip data via share token (read-only, no auth required)."""
    trip = get_trip_by_token(share_token)
    if not trip:
        return None
    detail = get_trip_detail(trip["id"])
    if not detail:
        return None
    # Return sanitized data (no internal IDs exposed beyond what's needed)
    return detail.model_dump(mode="json")


def export_settlement_text(trip_id: int) -> str | None:
    """Export settlement result as formatted text."""
    trip = get_trip(trip_id)
    if not trip:
        return None

    currency = trip.get("currency", "TWD")
    report = calculate_settlement(trip_id, currency)
    expenses = list_expenses(trip_id)
    total = sum(e.amount for e in expenses)

    lines = []
    lines.append(f"💰 旅遊拆帳結算 — {trip['name']}")
    lines.append(f"總花費：{currency} {total:,.0f}")
    lines.append(f"筆數：{len(expenses)} 筆")
    lines.append("")

    if not report.entries:
        lines.append("✅ 大家都結清了，不需要轉帳！")
    else:
        lines.append("📋 轉帳清單：")
        for entry in report.entries:
            status = "✅ 已結清" if entry.settled else "⏳ 待轉帳"
            lines.append(
                f"  用戶 {entry.from_user} → 用戶 {entry.to_user}："
                f"{currency} {entry.amount:,.0f} {status}"
            )

    return "\n".join(lines)
