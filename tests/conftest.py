"""Shared test fixtures.

Layer-specific conftests live under `tests/unit`, `tests/integration`,
and `tests/e2e`. This top-level file sets things that apply everywhere.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

# Tests must NEVER touch a real .env on the developer's machine. We seed
# safe defaults here before anything else imports settings.
os.environ.setdefault("APP_ENV", "local")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://flex:flex@localhost:5432/flex_test")
os.environ.setdefault("JWT_SECRET", "test-secret-min-32-characters-long-xxxxxxxxxx")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("NOTIFICATION_PROVIDER", "console")
os.environ.setdefault("PAYMENT_PROVIDER", "mock")
os.environ.setdefault("PAYMENT_WEBHOOK_SECRET", "test-webhook-secret-xxxxxx")


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Iterator[None]:
    """Drop the cached Settings between tests so env overrides take effect."""
    from src.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
