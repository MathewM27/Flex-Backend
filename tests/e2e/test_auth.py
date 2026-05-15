"""E2E tests for auth endpoints via ASGI + dependency overrides (no real DB)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.modules.auth.application.use_cases import GetCurrentUser, LoginUser, SignupUser
from src.modules.auth.interfaces.dependencies import (
    get_current_user_use_case,
    get_login_use_case,
    get_signup_use_case,
)
from tests.unit.auth.fakes import FakeJwtIssuer, FakePasswordHasher, FakeUserRepository


@pytest_asyncio.fixture
async def auth_client() -> AsyncIterator[AsyncClient]:
    from src.api.app import create_app

    app = create_app()
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    jwt = FakeJwtIssuer()

    app.dependency_overrides[get_signup_use_case] = lambda: SignupUser(repo=repo, hasher=hasher)
    app.dependency_overrides[get_login_use_case] = lambda: LoginUser(
        repo=repo, hasher=hasher, jwt=jwt
    )
    app.dependency_overrides[get_current_user_use_case] = lambda: GetCurrentUser(repo=repo)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()


_SIGNUP_PAYLOAD = {
    "email": "alice@flex.io",
    "password": "Secure1234!",
    "full_name": "Alice Smith",
    "role": "TENANT",
    "phone": "+254700000001",
}


class TestSignupEndpoint:
    @pytest.mark.asyncio
    async def test_returns_201_with_user_data(self, auth_client: AsyncClient) -> None:
        res = await auth_client.post("/api/v1/auth/signup", json=_SIGNUP_PAYLOAD)
        assert res.status_code == 201
        body = res.json()
        assert body["email"] == "alice@flex.io"
        assert body["role"] == "TENANT"
        assert UUID(body["id"])

    @pytest.mark.asyncio
    async def test_duplicate_email_returns_409(self, auth_client: AsyncClient) -> None:
        await auth_client.post("/api/v1/auth/signup", json=_SIGNUP_PAYLOAD)
        res = await auth_client.post("/api/v1/auth/signup", json=_SIGNUP_PAYLOAD)
        assert res.status_code == 409

    @pytest.mark.asyncio
    async def test_invalid_email_returns_422(self, auth_client: AsyncClient) -> None:
        payload = {**_SIGNUP_PAYLOAD, "email": "not-an-email"}
        res = await auth_client.post("/api/v1/auth/signup", json=payload)
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_short_password_returns_422(self, auth_client: AsyncClient) -> None:
        payload = {**_SIGNUP_PAYLOAD, "password": "short"}
        res = await auth_client.post("/api/v1/auth/signup", json=payload)
        assert res.status_code == 422


class TestLoginEndpoint:
    @pytest.mark.asyncio
    async def test_valid_credentials_return_token(self, auth_client: AsyncClient) -> None:
        await auth_client.post("/api/v1/auth/signup", json=_SIGNUP_PAYLOAD)
        res = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "alice@flex.io", "password": "Secure1234!"},
        )
        assert res.status_code == 200
        body = res.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_wrong_password_returns_401(self, auth_client: AsyncClient) -> None:
        await auth_client.post("/api/v1/auth/signup", json=_SIGNUP_PAYLOAD)
        res = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "alice@flex.io", "password": "WrongPass!"},
        )
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_unknown_email_returns_401(self, auth_client: AsyncClient) -> None:
        res = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@flex.io", "password": "Secure1234!"},
        )
        assert res.status_code == 401


class TestMeEndpoint:
    @pytest.mark.asyncio
    async def test_returns_current_user(self, auth_client: AsyncClient) -> None:
        # signup + login via fake implementations, then call /me with the fake token
        await auth_client.post("/api/v1/auth/signup", json=_SIGNUP_PAYLOAD)
        login_res = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "alice@flex.io", "password": "Secure1234!"},
        )
        token = login_res.json()["access_token"]
        # The FakeJwtIssuer issues "token:<uuid>"; override get_current_user to return
        # a fixed user so we don't need a real JWT decoder in this e2e test.
        from src.modules.auth.domain.entities import User
        from src.modules.auth.domain.role import Role
        from src.modules.auth.domain.value_objects import Email
        from src.modules.auth.interfaces.dependencies import get_current_user
        from src.shared.ids import new_id

        fixed_user = User(
            id=new_id(),
            email=Email("alice@flex.io"),
            password_hash="x",
            full_name="Alice Smith",
            role=Role.TENANT,
            phone="+254700000001",
        )
        # Retrieve the underlying app from the ASGI transport
        transport = auth_client._transport  # type: ignore[attr-defined]
        app = transport.app
        app.dependency_overrides[get_current_user] = lambda: fixed_user

        res = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["email"] == "alice@flex.io"

    @pytest.mark.asyncio
    async def test_missing_token_returns_401_or_403(self, auth_client: AsyncClient) -> None:
        # HTTPBearer returns 403 when no credentials are supplied
        res = await auth_client.get("/api/v1/auth/me")
        assert res.status_code in (401, 403)
