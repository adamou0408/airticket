"""API router — aggregates all endpoint modules."""

from fastapi import APIRouter

from app.api.tickets import router as tickets_router

api_router = APIRouter()

api_router.include_router(tickets_router)

# Trip endpoints will be added in Task 2.3
# Expense endpoints will be added in Task 4.2
# Auth endpoints will be added in Task 2.1
