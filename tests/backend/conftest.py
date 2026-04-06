"""Shared test fixtures — uses in-memory SQLite."""

import os

# Force SQLite for tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.database import create_tables, drop_tables, engine
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after. Reset in-memory stores."""
    await create_tables()
    yield
    await drop_tables()
    # Reset in-memory stores that aren't DB-backed yet
    from app.trips.comments import _reset as reset_comments
    from app.auth.service import _otp_store
    reset_comments()
    _otp_store.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
