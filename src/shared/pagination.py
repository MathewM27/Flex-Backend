"""Pagination envelope shared by every list endpoint (NFR-X4).

Shape:
    { "items": [...], "total": 123, "limit": 20, "offset": 0 }
"""

from collections.abc import Sequence
from dataclasses import dataclass

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: Sequence[T]
    total: int
    limit: int
    offset: int

    @classmethod
    def of(
        cls,
        items: Sequence[T],
        total: int,
        *,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> "Page[T]":
        return cls(items=items, total=total, limit=limit, offset=offset)


def clamp_limit(limit: int | None) -> int:
    """Apply the global limit policy. Used by interface-layer schemas."""
    if limit is None:
        return DEFAULT_LIMIT
    if limit < 1:
        return 1
    if limit > MAX_LIMIT:
        return MAX_LIMIT
    return limit
