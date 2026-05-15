"""FastAPI app factory.

Keeping construction in a factory (rather than module-level globals) makes
testing trivial: each test can build an app with its own settings and
dependency overrides.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.exception_handlers import register_exception_handlers
from src.api.middleware import RequestIdMiddleware
from src.api.routes import api_router
from src.core.config import Settings, get_settings
from src.core.db import dispose_engine
from src.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger.info("app_starting", env=settings.app_env, name=settings.app_name)
        yield
        await dispose_engine()
        logger.info("app_stopped")

    app = FastAPI(
        title="Flex Backend",
        version="0.1.0",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )

    # Order matters: RequestIdMiddleware first so every downstream log has it.
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(settings),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    return app


def _cors_origins(settings: Settings) -> list[str]:
    """Production must use an explicit allowlist; local can fall back to wildcard."""
    if settings.is_production:
        return settings.cors_origin_list
    return settings.cors_origin_list or ["*"]
