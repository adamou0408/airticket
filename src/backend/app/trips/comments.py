"""Comments and edit history for trip items.

Spec: specs/travel-planner-app/spec.md — US-7
Task: 3.2 — Comment/discussion on itinerary items
Task: 3.3 — Edit history tracking
"""

from datetime import datetime, timezone
from pydantic import BaseModel, Field

# In-memory stores
_comments: dict[int, list[dict]] = {}  # item_id -> [comments]
_edit_history: list[dict] = []
_next_comment_id = 1


def _reset():
    global _next_comment_id
    _comments.clear()
    _edit_history.clear()
    _next_comment_id = 1


class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1)


class Comment(BaseModel):
    id: int
    item_id: int
    user_id: int
    text: str
    created_at: str


class EditRecord(BaseModel):
    trip_id: int
    item_id: int | None = None
    user_id: int
    action: str  # "add_item", "update_item", "delete_item", "add_comment", "reorder", "finalize"
    detail: str
    created_at: str


def add_comment(item_id: int, user_id: int, text: str) -> Comment:
    global _next_comment_id
    now = datetime.now(timezone.utc).isoformat()
    comment = {
        "id": _next_comment_id,
        "item_id": item_id,
        "user_id": user_id,
        "text": text,
        "created_at": now,
    }
    _comments.setdefault(item_id, []).append(comment)
    _next_comment_id += 1
    return Comment(**comment)


def get_comments(item_id: int) -> list[Comment]:
    return [Comment(**c) for c in _comments.get(item_id, [])]


def record_edit(trip_id: int, user_id: int, action: str, detail: str, item_id: int | None = None):
    now = datetime.now(timezone.utc).isoformat()
    _edit_history.append({
        "trip_id": trip_id,
        "item_id": item_id,
        "user_id": user_id,
        "action": action,
        "detail": detail,
        "created_at": now,
    })


def get_edit_history(trip_id: int) -> list[EditRecord]:
    return [EditRecord(**e) for e in _edit_history if e["trip_id"] == trip_id]
