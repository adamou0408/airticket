"""API router — aggregates all endpoint modules."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.expenses import router as expenses_router
from app.api.share import router as share_router
from app.api.tickets import router as tickets_router
from app.api.trips import router as trips_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(tickets_router)
api_router.include_router(trips_router)
api_router.include_router(expenses_router)
api_router.include_router(share_router)
