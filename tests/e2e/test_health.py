"""Foundational smoke test: app boots, health works, error envelope works."""

from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_response_carries_request_id_header(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    rid = response.headers.get("X-Request-Id")
    assert rid is not None
    UUID(rid)  # parseable


@pytest.mark.asyncio
async def test_request_id_header_is_echoed_back(client: AsyncClient) -> None:
    incoming = "01900000-0000-7000-8000-000000000abc"
    response = await client.get("/api/v1/health", headers={"X-Request-Id": incoming})
    assert response.headers["X-Request-Id"] == incoming


@pytest.mark.asyncio
async def test_unknown_route_returns_error_envelope(client: AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body == {"error": {"code": "NOT_FOUND", "message": "Not Found"}}
