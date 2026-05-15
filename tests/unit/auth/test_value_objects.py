"""Unit tests for Email and Password value objects (FR-A1, FR-A2, NFR-S1)."""

from __future__ import annotations

import pytest

from src.modules.auth.domain.value_objects import Email, Password

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------


class TestEmail:
    def test_valid_email_is_accepted(self) -> None:
        email = Email("User@Example.COM")
        assert email.value == "user@example.com"

    def test_email_is_normalised_to_lowercase(self) -> None:
        assert Email("ALICE@FLEX.IO").value == "alice@flex.io"

    def test_email_strips_whitespace(self) -> None:
        assert Email("  bob@flex.io  ").value == "bob@flex.io"

    def test_missing_at_sign_raises(self) -> None:
        with pytest.raises(ValueError, match="email"):
            Email("notanemail")

    def test_missing_domain_raises(self) -> None:
        with pytest.raises(ValueError, match="email"):
            Email("user@")

    def test_missing_local_raises(self) -> None:
        with pytest.raises(ValueError, match="email"):
            Email("@domain.com")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValueError, match="email"):
            Email("")

    def test_equality_is_value_based(self) -> None:
        assert Email("alice@flex.io") == Email("ALICE@FLEX.IO")

    def test_hash_is_consistent_with_equality(self) -> None:
        assert hash(Email("alice@flex.io")) == hash(Email("ALICE@FLEX.IO"))

    def test_repr_does_not_expose_raw_input(self) -> None:
        r = repr(Email("alice@flex.io"))
        assert "alice@flex.io" in r

    def test_email_with_plus_addressing_is_valid(self) -> None:
        email = Email("alice+tag@flex.io")
        assert email.value == "alice+tag@flex.io"


# ---------------------------------------------------------------------------
# Password
# ---------------------------------------------------------------------------


class TestPassword:
    def test_valid_password_is_accepted(self) -> None:
        pwd = Password("Secure1234!")
        assert pwd.value == "Secure1234!"

    def test_too_short_raises(self) -> None:
        with pytest.raises(ValueError, match="8"):
            Password("Short1!")

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="8"):
            Password("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError, match="8"):
            Password("       ")

    def test_exactly_8_chars_is_accepted(self) -> None:
        Password("Abcdef1!")

    def test_password_is_not_trimmed(self) -> None:
        pwd = Password("  Secure1234!  ")
        assert pwd.value == "  Secure1234!  "

    def test_equality_is_value_based(self) -> None:
        assert Password("Secure1234!") == Password("Secure1234!")

    def test_different_passwords_not_equal(self) -> None:
        assert Password("Secure1234!") != Password("Other5678@")

    def test_repr_does_not_expose_value(self) -> None:
        r = repr(Password("Secure1234!"))
        assert "Secure1234!" not in r
        assert "Password" in r
