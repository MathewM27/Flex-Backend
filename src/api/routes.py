"""Mounts the `/api/v1` router and the health endpoints.

Module routers are imported and included here once each module exists.
For the foundation commit only `/health` and `/ready` are live.
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.core.db import get_engine

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/health", tags=["meta"], summary="Liveness probe")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@api_router.get("/ready", tags=["meta"], summary="Readiness probe (DB ping)")
async def ready() -> dict[str, str]:
    """Verifies the DB is reachable; used by k8s/compose readiness checks."""
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except SQLAlchemyError as exc:  # pragma: no cover — exercised in integration
        return {"status": "degraded", "detail": str(exc)}
