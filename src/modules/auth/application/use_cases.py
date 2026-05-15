"""Auth application use cases (FR-A1 - FR-A6)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.modules.auth.domain.entities import User
from src.modules.auth.domain.ports import JwtIssuer, PasswordHasher, UserRepository
from src.modules.auth.domain.role import Role
from src.modules.auth.domain.value_objects import Email, Password
from src.shared.errors import ConflictError, NotFoundError, UnauthorizedError
from src.shared.ids import new_id


@dataclass(frozen=True)
class SignupUserCommand:
    email: str
    password: str
    full_name: str
    role: Role
    phone: str


@dataclass(frozen=True)
class LoginUserCommand:
    email: str
    password: str


class SignupUser:
    def __init__(self, *, repo: UserRepository, hasher: PasswordHasher) -> None:
        self._repo = repo
        self._hasher = hasher

    async def execute(self, cmd: SignupUserCommand) -> UUID:
        email = Email(cmd.email)
        existing = await self._repo.get_by_email(email)
        if existing is not None:
            raise ConflictError(f"A user with email {cmd.email!r} already exists.")

        password = Password(cmd.password)
        user = User(
            id=new_id(),
            email=email,
            password_hash=self._hasher.hash(password.value),
            full_name=cmd.full_name,
            role=cmd.role,
            phone=cmd.phone,
        )
        await self._repo.save(user)
        return user.id


class LoginUser:
    def __init__(self, *, repo: UserRepository, hasher: PasswordHasher, jwt: JwtIssuer) -> None:
        self._repo = repo
        self._hasher = hasher
        self._jwt = jwt

    async def execute(self, cmd: LoginUserCommand) -> str:
        email = Email(cmd.email)
        user = await self._repo.get_by_email(email)
        if user is None or not self._hasher.verify(cmd.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")
        return self._jwt.issue(user)


class GetCurrentUser:
    def __init__(self, *, repo: UserRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID) -> User:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id!r} not found.")
        return user
