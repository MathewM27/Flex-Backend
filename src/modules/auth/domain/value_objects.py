"""Auth domain value objects: Email and Password (FR-A1, FR-A2, NFR-S1)."""

from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MIN_PASSWORD_LEN = 8


class Email:
    """Normalised, validated e-mail address."""

    __slots__ = ("_value",)

    def __init__(self, raw: str) -> None:
        normalised = raw.strip().lower()
        if not _EMAIL_RE.match(normalised):
            raise ValueError(f"Invalid email address: {raw!r}")
        self._value = normalised

    @property
    def value(self) -> str:
        return self._value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Email) and self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __repr__(self) -> str:
        return f"Email({self._value!r})"


class Password:
    """Plaintext password — validated but never hashed here (hashing is an infra concern)."""

    __slots__ = ("_value",)

    def __init__(self, raw: str) -> None:
        if len(raw) < _MIN_PASSWORD_LEN:
            raise ValueError(f"Password must be at least {_MIN_PASSWORD_LEN} characters long.")
        self._value = raw

    @property
    def value(self) -> str:
        return self._value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Password) and self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __repr__(self) -> str:
        return "Password(***)"
