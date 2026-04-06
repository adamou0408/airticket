"""API router — aggregates all endpoint modules."""

from fastapi import APIRouter

from app.api.airports import router as airports_router
from app.api.auth import router as auth_router
from app.api.expenses import router as expenses_router
from app.api.flights import router as flights_router
from app.api.share import router as share_router
from app.api.tickets import router as tickets_router
from app.api.trips import router as trips_router

api_router = APIRouter()

api_router.include_router(airports_router)
api_router.include_router(auth_router)
api_router.include_router(flights_router)
api_router.include_router(tickets_router)
api_router.include_router(trips_router)
api_router.include_router(expenses_router)
api_router.include_router(share_router)
