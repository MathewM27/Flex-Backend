"""Unit tests for User entity and Role enum (FR-A1, FR-A5)."""

from __future__ import annotations

from datetime import UTC
from uuid import UUID

import pytest

from src.modules.auth.domain.entities import User
from src.modules.auth.domain.role import Role
from src.modules.auth.domain.value_objects import Email

_ID_A = UUID("00000000-0000-7000-8000-000000000001")
_ID_B = UUID("00000000-0000-7000-8000-000000000002")


def _make_user(**overrides: object) -> User:
    defaults: dict[str, object] = {
        "id": _ID_A,
        "email": Email("alice@flex.io"),
        "password_hash": "$2b$12$hashedvalue",
        "full_name": "Alice Smith",
        "role": Role.TENANT,
        "phone": "+254700000001",
    }
    defaults.update(overrides)
    return User(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Role enum
# ---------------------------------------------------------------------------


class TestRole:
    def test_tenant_value(self) -> None:
        assert Role.TENANT.value == "TENANT"

    def test_landlord_value(self) -> None:
        assert Role.LANDLORD.value == "LANDLORD"

    def test_only_two_roles(self) -> None:
        assert set(Role) == {Role.TENANT, Role.LANDLORD}


# ---------------------------------------------------------------------------
# User construction
# ---------------------------------------------------------------------------


class TestUserConstruction:
    def test_create_tenant(self) -> None:
        user = _make_user()
        assert user.id == _ID_A
        assert user.email == Email("alice@flex.io")
        assert user.role == Role.TENANT
        assert user.full_name == "Alice Smith"
        assert user.phone == "+254700000001"

    def test_create_landlord(self) -> None:
        user = _make_user(role=Role.LANDLORD)
        assert user.role == Role.LANDLORD

    def test_password_hash_stored(self) -> None:
        user = _make_user(password_hash="$2b$12$xyz")
        assert user.password_hash == "$2b$12$xyz"

    def test_user_has_created_at(self) -> None:
        from datetime import datetime

        user = _make_user()
        assert isinstance(user.created_at, datetime)
        assert user.created_at.tzinfo == UTC

    def test_empty_full_name_raises(self) -> None:
        with pytest.raises(ValueError, match="full_name"):
            _make_user(full_name="   ")

    def test_phone_must_start_with_plus(self) -> None:
        with pytest.raises(ValueError, match="phone"):
            _make_user(phone="0700000001")

    def test_phone_must_be_digits_after_plus(self) -> None:
        with pytest.raises(ValueError, match="phone"):
            _make_user(phone="+2547abc")


# ---------------------------------------------------------------------------
# User equality / identity
# ---------------------------------------------------------------------------


class TestUserIdentity:
    def test_same_id_means_equal(self) -> None:
        a = _make_user(id=_ID_A, email=Email("a@flex.io"))
        b = _make_user(id=_ID_A, email=Email("b@flex.io"))
        assert a == b

    def test_different_id_means_not_equal(self) -> None:
        a = _make_user(id=_ID_A)
        b = _make_user(id=_ID_B)
        assert a != b

    def test_hash_based_on_id(self) -> None:
        a = _make_user(id=_ID_A)
        b = _make_user(id=_ID_A)
        assert hash(a) == hash(b)
