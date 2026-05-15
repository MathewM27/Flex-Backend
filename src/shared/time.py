"""Time handling (NFR-X2).

Rules:
- All datetimes are UTC, timezone-aware. Naive datetimes are forbidden.
- "Now" is read from a `Clock` port. Tests inject `FixedClock`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol


def ensure_aware_utc(value: datetime) -> datetime:
    """Validate that a datetime is timezone-aware and in UTC. Returns the value unchanged."""
    if value.tzinfo is None:
        raise ValueError("naive datetimes are forbidden; supply tzinfo=UTC")
    if value.utcoffset() != value.astimezone(UTC).utcoffset():
        # not strictly required (Python normalizes), but explicit
        return value.astimezone(UTC)
    return value


class Clock(Protocol):
    def now(self) -> datetime:  # always UTC-aware
        ...


class SystemClock:
    """Production clock. Reads real wall-clock time in UTC."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    """Deterministic clock for tests. Time only advances when `set()` is called."""

    def __init__(self, instant: datetime) -> None:
        self._instant = ensure_aware_utc(instant)

    def now(self) -> datetime:
        return self._instant

    def set(self, instant: datetime) -> None:
        self._instant = ensure_aware_utc(instant)
