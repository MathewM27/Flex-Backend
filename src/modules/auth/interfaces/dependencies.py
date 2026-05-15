"""FastAPI dependency providers for auth (NFR-A3)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.db import get_session
from src.modules.auth.application.use_cases import GetCurrentUser, LoginUser, SignupUser
from src.modules.auth.domain.entities import User
from src.modules.auth.infrastructure.repositories import SqlAlchemyUserRepository
from src.modules.auth.infrastructure.security import BcryptPasswordHasher, JoseJwtIssuer
from src.shared.errors import NotFoundError

_bearer = HTTPBearer()


def _jwt_issuer(settings: Annotated[Settings, Depends(get_settings)]) -> JoseJwtIssuer:
    return JoseJwtIssuer(
        secret=settings.jwt_secret,
        expires_minutes=settings.jwt_expires_minutes,
    )


def _hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher()


async def get_signup_use_case(
    session: Annotated[AsyncSession, Depends(get_session)],
    hasher: Annotated[BcryptPasswordHasher, Depends(_hasher)],
) -> SignupUser:
    return SignupUser(repo=SqlAlchemyUserRepository(session), hasher=hasher)


async def get_login_use_case(
    session: Annotated[AsyncSession, Depends(get_session)],
    hasher: Annotated[BcryptPasswordHasher, Depends(_hasher)],
    jwt: Annotated[JoseJwtIssuer, Depends(_jwt_issuer)],
) -> LoginUser:
    return LoginUser(repo=SqlAlchemyUserRepository(session), hasher=hasher, jwt=jwt)


async def get_current_user_use_case(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GetCurrentUser:
    return GetCurrentUser(repo=SqlAlchemyUserRepository(session))


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    jwt: Annotated[JoseJwtIssuer, Depends(_jwt_issuer)],
    get_me: Annotated[GetCurrentUser, Depends(get_current_user_use_case)],
) -> User:
    try:
        payload = jwt.decode(credentials.credentials)
        user_id = UUID(str(payload["sub"]))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token."
        ) from exc
    try:
        return await get_me.execute(user_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found."
        ) from exc
