"""Bcrypt password hasher and JWT issuer (NFR-S1, FR-A3)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from src.modules.auth.domain.entities import User


class BcryptPasswordHasher:
    """bcrypt with work factor ≥ 12 (NFR-S1)."""

    _ROUNDS = 12

    def hash(self, plaintext: str) -> str:
        return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt(rounds=self._ROUNDS)).decode()

    def verify(self, plaintext: str, hashed: str) -> bool:
        return bcrypt.checkpw(plaintext.encode(), hashed.encode())


class JoseJwtIssuer:
    """PyJWT-backed issuer. Token payload: sub, role, exp (FR-A3)."""

    _ALGORITHM = "HS256"

    def __init__(self, secret: str, expires_minutes: int = 1440) -> None:
        self._secret = secret
        self._expires_minutes = expires_minutes

    def issue(self, user: User) -> str:
        payload = {
            "sub": str(user.id),
            "role": user.role.value,
            "exp": datetime.now(UTC) + timedelta(minutes=self._expires_minutes),
        }
        return jwt.encode(payload, self._secret, algorithm=self._ALGORITHM)

    def decode(self, token: str) -> dict[str, object]:
        return jwt.decode(token, self._secret, algorithms=[self._ALGORITHM])
