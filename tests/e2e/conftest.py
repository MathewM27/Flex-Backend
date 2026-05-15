"""Fixtures for end-to-end tests."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """An httpx client wired to the FastAPI app via ASGI (no real network)."""
    from src.api.app import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
