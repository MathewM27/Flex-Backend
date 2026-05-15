"""Pagination envelope — NFR-X4."""

from __future__ import annotations

from src.shared.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page, clamp_limit


def test_page_of_carries_total_and_offset() -> None:
    page = Page.of(items=[1, 2, 3], total=42, limit=10, offset=20)
    assert page.items == [1, 2, 3]
    assert page.total == 42
    assert page.limit == 10
    assert page.offset == 20


def test_clamp_limit_applies_defaults_and_bounds() -> None:
    assert clamp_limit(None) == DEFAULT_LIMIT
    assert clamp_limit(0) == 1
    assert clamp_limit(50) == 50
    assert clamp_limit(MAX_LIMIT + 100) == MAX_LIMIT
