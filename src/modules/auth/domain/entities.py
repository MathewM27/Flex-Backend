"""Auth domain entities (FR-A1)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import UUID

from src.modules.auth.domain.role import Role
from src.modules.auth.domain.value_objects import Email

_E164_RE = re.compile(r"^\+\d{7,15}$")


class User:
    """User aggregate root."""

    def __init__(
        self,
        *,
        id: UUID,  # noqa: A002
        email: Email,
        password_hash: str,
        full_name: str,
        role: Role,
        phone: str,
        created_at: datetime | None = None,
    ) -> None:
        if not full_name.strip():
            raise ValueError("full_name must not be blank.")
        if not _E164_RE.match(phone):
            raise ValueError(f"phone must be E.164 format (e.g. +254700000001), got {phone!r}.")

        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name.strip()
        self.role = role
        self.phone = phone
        self.created_at: datetime = created_at or datetime.now(UTC)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, User) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r}, role={self.role!r})"
