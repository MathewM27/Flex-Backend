"""Unit tests for BcryptPasswordHasher and JoseJwtIssuer."""

from __future__ import annotations

import jwt as pyjwt
import pytest

from src.modules.auth.infrastructure.security import BcryptPasswordHasher, JoseJwtIssuer
from tests.unit.auth.test_user_entity import _make_user

_SECRET = "super-secret-jwt-key-for-tests-only-32chars"


class TestBcryptPasswordHasher:
    def test_hash_is_not_plaintext(self) -> None:
        hasher = BcryptPasswordHasher()
        assert hasher.hash("Secure1234!") != "Secure1234!"

    def test_verify_correct_password(self) -> None:
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("Secure1234!")
        assert hasher.verify("Secure1234!", hashed) is True

    def test_verify_wrong_password(self) -> None:
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("Secure1234!")
        assert hasher.verify("WrongPass!", hashed) is False

    def test_two_hashes_of_same_plaintext_differ(self) -> None:
        hasher = BcryptPasswordHasher()
        assert hasher.hash("Secure1234!") != hasher.hash("Secure1234!")


class TestJoseJwtIssuer:
    def test_issue_returns_string(self) -> None:
        issuer = JoseJwtIssuer(secret=_SECRET)
        token = issuer.issue(_make_user())
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_returns_sub_and_role(self) -> None:
        issuer = JoseJwtIssuer(secret=_SECRET)
        user = _make_user()
        token = issuer.issue(user)
        payload = issuer.decode(token)
        assert str(payload["sub"]) == str(user.id)
        assert payload["role"] == user.role.value

    def test_tampered_token_raises(self) -> None:
        issuer = JoseJwtIssuer(secret=_SECRET)
        token = issuer.issue(_make_user())
        with pytest.raises(pyjwt.PyJWTError):
            issuer.decode(token + "tampered")

    def test_wrong_secret_raises(self) -> None:
        issuer = JoseJwtIssuer(secret=_SECRET)
        token = issuer.issue(_make_user())
        other = JoseJwtIssuer(secret=_SECRET + "-different")
        with pytest.raises(pyjwt.PyJWTError):
            other.decode(token)
