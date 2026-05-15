"""UUIDv7 generation + deterministic test factory — NFR-X1, NFR-T6."""

from __future__ import annotations

from uuid import UUID

import pytest

from src.shared.ids import DeterministicUUIDFactory, new_id


def test_new_id_returns_uuid_with_version_7() -> None:
    value = new_id()
    assert isinstance(value, UUID)
    assert value.version == 7


def test_new_id_is_monotonically_increasing_over_calls() -> None:
    """UUIDv7 embeds a millisecond timestamp; sequential calls should not decrease."""
    a = new_id()
    b = new_id()
    assert str(b) >= str(a)  # string compare works because v7 is lex-orderable


def test_deterministic_factory_emits_values_in_order() -> None:
    a = UUID("00000000-0000-7000-8000-000000000001")
    b = UUID("00000000-0000-7000-8000-000000000002")
    factory = DeterministicUUIDFactory(a, b)
    assert factory() == a
    assert factory() == b


def test_deterministic_factory_raises_when_exhausted() -> None:
    factory = DeterministicUUIDFactory("00000000-0000-7000-8000-000000000001")
    factory()
    with pytest.raises(RuntimeError, match="exhausted"):
        factory()
