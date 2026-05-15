"""In-memory fakes for auth use-case tests."""

from __future__ import annotations

from uuid import UUID

from src.modules.auth.domain.entities import User
from src.modules.auth.domain.value_objects import Email


class FakeUserRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, User] = {}

    async def save(self, user: User) -> None:
        self._by_id[user.id] = user

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._by_id.get(user_id)

    async def get_by_email(self, email: Email) -> User | None:
        return next((u for u in self._by_id.values() if u.email == email), None)


class FakePasswordHasher:
    def hash(self, plaintext: str) -> str:
        return f"hashed:{plaintext}"

    def verify(self, plaintext: str, hashed: str) -> bool:
        return hashed == f"hashed:{plaintext}"


class FakeJwtIssuer:
    def issue(self, user: User) -> str:
        return f"token:{user.id}"

    def decode(self, token: str) -> dict[str, object]:
        _, user_id = token.split(":", 1)
        return {"sub": user_id}
