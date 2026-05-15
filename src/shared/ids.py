"""ID generation (NFR-X1).

UUIDv7 is time-ordered and B-tree friendly. Generated via the `UUIDFactory`
port so tests can produce deterministic sequences.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

import uuid_utils


class UUIDFactory(Protocol):
    def __call__(self) -> UUID: ...


def new_id() -> UUID:
    """Production factory — wall-clock-based UUIDv7."""
    return UUID(str(uuid_utils.uuid7()))


class DeterministicUUIDFactory:
    """Test factory that emits a controlled sequence of ids."""

    def __init__(self, *values: UUID | str) -> None:
        self._values: list[UUID] = [v if isinstance(v, UUID) else UUID(v) for v in values]
        self._index = 0

    def __call__(self) -> UUID:
        if self._index >= len(self._values):
            raise RuntimeError("DeterministicUUIDFactory exhausted")
        value = self._values[self._index]
        self._index += 1
        return value
