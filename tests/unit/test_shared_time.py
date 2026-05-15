"""Clock + UTC enforcement — NFR-X2, NFR-T6."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from src.shared.time import FixedClock, SystemClock, ensure_aware_utc


def test_ensure_aware_utc_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="naive"):
        ensure_aware_utc(datetime(2026, 1, 1))


def test_ensure_aware_utc_normalizes_non_utc_timezone() -> None:
    tokyo = timezone(timedelta(hours=9))
    value = datetime(2026, 1, 1, 18, 0, tzinfo=tokyo)
    result = ensure_aware_utc(value)
    assert result.tzinfo == UTC
    assert result.hour == 9  # 18:00 Tokyo == 09:00 UTC


def test_system_clock_returns_aware_utc() -> None:
    now = SystemClock().now()
    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)


def test_fixed_clock_returns_set_instant() -> None:
    instant = datetime(2026, 5, 15, 12, 0, tzinfo=UTC)
    clock = FixedClock(instant)
    assert clock.now() == instant
    new_instant = datetime(2026, 6, 1, 8, 0, tzinfo=UTC)
    clock.set(new_instant)
    assert clock.now() == new_instant
