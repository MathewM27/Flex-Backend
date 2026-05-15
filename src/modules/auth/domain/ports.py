"""Auth domain ports — interfaces that infrastructure must implement (NFR-A4)."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.modules.auth.domain.entities import User
from src.modules.auth.domain.value_objects import Email


class UserRepository(Protocol):
    async def save(self, user: User) -> None: ...

    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def get_by_email(self, email: Email) -> User | None: ...


class PasswordHasher(Protocol):
    def hash(self, plaintext: str) -> str: ...

    def verify(self, plaintext: str, hashed: str) -> bool: ...


class JwtIssuer(Protocol):
    def issue(self, user: User) -> str: ...

    def decode(self, token: str) -> dict[str, object]: ...
