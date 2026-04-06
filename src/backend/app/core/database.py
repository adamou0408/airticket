"""Database engine and session management.

Supports:
- PostgreSQL (production): DATABASE_URL=postgresql+asyncpg://...
- SQLite (dev/test): DATABASE_URL=sqlite+aiosqlite:///./airticket.db
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

_connect_args = {}
if "sqlite" in settings.database_url:
    _connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args=_connect_args,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


async def create_tables():
    """Create all tables. Call on startup."""
    from app.core import models  # noqa: F401 — register models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all tables. For testing only."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
