"""Unit tests for auth use cases with in-memory fakes (FR-A1 - FR-A6)."""

from __future__ import annotations

import pytest

from src.modules.auth.application.use_cases import (
    GetCurrentUser,
    LoginUser,
    LoginUserCommand,
    SignupUser,
    SignupUserCommand,
)
from src.modules.auth.domain.role import Role
from src.modules.auth.domain.value_objects import Email
from src.shared.errors import ConflictError, NotFoundError, UnauthorizedError
from tests.unit.auth.fakes import FakeJwtIssuer, FakePasswordHasher, FakeUserRepository

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def hasher() -> FakePasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def jwt() -> FakeJwtIssuer:
    return FakeJwtIssuer()


@pytest.fixture
def signup(repo: FakeUserRepository, hasher: FakePasswordHasher) -> SignupUser:
    return SignupUser(repo=repo, hasher=hasher)


@pytest.fixture
def login(repo: FakeUserRepository, hasher: FakePasswordHasher, jwt: FakeJwtIssuer) -> LoginUser:
    return LoginUser(repo=repo, hasher=hasher, jwt=jwt)


@pytest.fixture
def get_me(repo: FakeUserRepository) -> GetCurrentUser:
    return GetCurrentUser(repo=repo)


# ---------------------------------------------------------------------------
# SignupUser
# ---------------------------------------------------------------------------


class TestSignupUser:
    @pytest.mark.asyncio
    async def test_creates_user_and_returns_id(
        self, signup: SignupUser, repo: FakeUserRepository
    ) -> None:
        cmd = SignupUserCommand(
            email="alice@flex.io",
            password="Secure1234!",
            full_name="Alice Smith",
            role=Role.TENANT,
            phone="+254700000001",
        )
        user_id = await signup.execute(cmd)
        saved = await repo.get_by_id(user_id)
        assert saved is not None
        assert saved.email == Email("alice@flex.io")

    @pytest.mark.asyncio
    async def test_password_is_hashed(self, signup: SignupUser, repo: FakeUserRepository) -> None:
        cmd = SignupUserCommand(
            email="alice@flex.io",
            password="Secure1234!",
            full_name="Alice Smith",
            role=Role.TENANT,
            phone="+254700000001",
        )
        user_id = await signup.execute(cmd)
        user = await repo.get_by_id(user_id)
        assert user is not None
        assert user.password_hash != "Secure1234!"
        assert user.password_hash.startswith("hashed:")

    @pytest.mark.asyncio
    async def test_duplicate_email_raises_conflict(self, signup: SignupUser) -> None:
        cmd = SignupUserCommand(
            email="alice@flex.io",
            password="Secure1234!",
            full_name="Alice Smith",
            role=Role.TENANT,
            phone="+254700000001",
        )
        await signup.execute(cmd)
        with pytest.raises(ConflictError, match="email"):
            await signup.execute(cmd)

    @pytest.mark.asyncio
    async def test_role_is_persisted(self, signup: SignupUser, repo: FakeUserRepository) -> None:
        cmd = SignupUserCommand(
            email="bob@flex.io",
            password="Secure1234!",
            full_name="Bob Jones",
            role=Role.LANDLORD,
            phone="+254700000002",
        )
        user_id = await signup.execute(cmd)
        user = await repo.get_by_id(user_id)
        assert user is not None
        assert user.role == Role.LANDLORD


# ---------------------------------------------------------------------------
# LoginUser
# ---------------------------------------------------------------------------


class TestLoginUser:
    @pytest.mark.asyncio
    async def test_valid_credentials_return_token(
        self,
        signup: SignupUser,
        login: LoginUser,
    ) -> None:
        await signup.execute(
            SignupUserCommand(
                email="alice@flex.io",
                password="Secure1234!",
                full_name="Alice Smith",
                role=Role.TENANT,
                phone="+254700000001",
            )
        )
        token = await login.execute(LoginUserCommand(email="alice@flex.io", password="Secure1234!"))
        assert token.startswith("token:")

    @pytest.mark.asyncio
    async def test_unknown_email_raises_unauthorized(self, login: LoginUser) -> None:
        with pytest.raises(UnauthorizedError):
            await login.execute(LoginUserCommand(email="ghost@flex.io", password="Secure1234!"))

    @pytest.mark.asyncio
    async def test_wrong_password_raises_unauthorized(
        self, signup: SignupUser, login: LoginUser
    ) -> None:
        await signup.execute(
            SignupUserCommand(
                email="alice@flex.io",
                password="Secure1234!",
                full_name="Alice Smith",
                role=Role.TENANT,
                phone="+254700000001",
            )
        )
        with pytest.raises(UnauthorizedError):
            await login.execute(LoginUserCommand(email="alice@flex.io", password="WrongPass!"))


# ---------------------------------------------------------------------------
# GetCurrentUser
# ---------------------------------------------------------------------------


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_returns_user_for_valid_id(
        self, signup: SignupUser, get_me: GetCurrentUser
    ) -> None:
        user_id = await signup.execute(
            SignupUserCommand(
                email="alice@flex.io",
                password="Secure1234!",
                full_name="Alice Smith",
                role=Role.TENANT,
                phone="+254700000001",
            )
        )
        user = await get_me.execute(user_id)
        assert user.id == user_id

    @pytest.mark.asyncio
    async def test_unknown_id_raises_not_found(self, get_me: GetCurrentUser) -> None:
        from src.shared.ids import new_id

        with pytest.raises(NotFoundError):
            await get_me.execute(new_id())
