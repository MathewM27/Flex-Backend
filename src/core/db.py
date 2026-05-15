"""Async SQLAlchemy engine and session factory.

Sessions are produced via `get_session()` (FastAPI dependency) and never
shared across requests. The Unit-of-Work adapter (see
`src/shared/unit_of_work.py`) wraps a session for the application layer.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_settings


def build_engine(dsn: str | None = None) -> AsyncEngine:
    """Create a new engine. Tests use this to build per-test engines."""
    settings = get_settings()
    return create_async_engine(
        dsn or settings.database_url,
        echo=False,
        pool_pre_ping=True,
        future=True,
    )


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = build_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency. Yields one session per request, commits on success."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Called at app shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
