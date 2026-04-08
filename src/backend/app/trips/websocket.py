"""WebSocket connection manager for real-time trip editing.

Spec: .req/specs/travel-planner-app/spec.md — US-7 (共同編輯行程)
Task: .req/specs/travel-planner-app/tasks.md — Task 3.1 (WebSocket 即時同步)

Manages WebSocket connections grouped by trip_id, broadcasts edit events
to all connected members of a trip.
"""

import asyncio
import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections per trip.

    Structure:
        active[trip_id] = [list of WebSocket]

    Broadcast events to all connected clients editing the same trip.
    """

    def __init__(self):
        self.active: dict[int, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, trip_id: int, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            if trip_id not in self.active:
                self.active[trip_id] = []
            self.active[trip_id].append(websocket)
        # Notify others about presence
        await self.broadcast(trip_id, {
            "type": "presence",
            "action": "join",
            "count": len(self.active[trip_id]),
        }, exclude=websocket)

    async def disconnect(self, trip_id: int, websocket: WebSocket):
        async with self._lock:
            if trip_id in self.active and websocket in self.active[trip_id]:
                self.active[trip_id].remove(websocket)
                if not self.active[trip_id]:
                    del self.active[trip_id]
        # Notify others
        if trip_id in self.active:
            await self.broadcast(trip_id, {
                "type": "presence",
                "action": "leave",
                "count": len(self.active.get(trip_id, [])),
            })

    async def broadcast(self, trip_id: int, message: dict, exclude: WebSocket | None = None):
        """Broadcast a JSON message to all connected clients for a trip."""
        connections = self.active.get(trip_id, [])
        if not connections:
            return

        payload = json.dumps(message)
        dead = []
        for conn in connections:
            if conn is exclude:
                continue
            try:
                await conn.send_text(payload)
            except Exception:
                dead.append(conn)

        # Clean up dead connections
        if dead:
            async with self._lock:
                for d in dead:
                    if d in self.active.get(trip_id, []):
                        self.active[trip_id].remove(d)

    def get_connection_count(self, trip_id: int) -> int:
        return len(self.active.get(trip_id, []))


# Global singleton
manager = ConnectionManager()


async def notify_item_added(trip_id: int, item: dict, user_id: int):
    """Called when an itinerary item is added — notify all editors."""
    await manager.broadcast(trip_id, {
        "type": "item_added",
        "item": item,
        "user_id": user_id,
    })


async def notify_item_updated(trip_id: int, item: dict, user_id: int):
    """Called when an itinerary item is updated."""
    await manager.broadcast(trip_id, {
        "type": "item_updated",
        "item": item,
        "user_id": user_id,
    })


async def notify_item_deleted(trip_id: int, item_id: int, user_id: int):
    """Called when an itinerary item is deleted."""
    await manager.broadcast(trip_id, {
        "type": "item_deleted",
        "item_id": item_id,
        "user_id": user_id,
    })


async def notify_trip_finalized(trip_id: int, user_id: int):
    """Called when trip status changes to finalized."""
    await manager.broadcast(trip_id, {
        "type": "trip_finalized",
        "user_id": user_id,
    })


async def notify_comment_added(trip_id: int, item_id: int, comment: dict):
    """Called when a comment is added to an itinerary item."""
    await manager.broadcast(trip_id, {
        "type": "comment_added",
        "item_id": item_id,
        "comment": comment,
    })
