"""SQLAlchemy implementation of UserRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities import User
from src.modules.auth.domain.value_objects import Email
from src.modules.auth.infrastructure.orm import UserRow


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: User) -> None:
        row = await self._session.get(UserRow, user.id)
        if row is None:
            row = UserRow(
                id=user.id,
                email=user.email.value,
                password_hash=user.password_hash,
                full_name=user.full_name,
                role=user.role,
                phone=user.phone,
                created_at=user.created_at,
            )
            self._session.add(row)
        else:
            row.email = user.email.value
            row.password_hash = user.password_hash
            row.full_name = user.full_name
            row.role = user.role
            row.phone = user.phone
        await self._session.flush()

    async def get_by_id(self, user_id: UUID) -> User | None:
        row = await self._session.get(UserRow, user_id)
        return _to_entity(row) if row else None

    async def get_by_email(self, email: Email) -> User | None:
        result = await self._session.execute(select(UserRow).where(UserRow.email == email.value))
        row = result.scalar_one_or_none()
        return _to_entity(row) if row else None


def _to_entity(row: UserRow) -> User:
    return User(
        id=row.id,
        email=Email(row.email),
        password_hash=row.password_hash,
        full_name=row.full_name,
        role=row.role,
        phone=row.phone,
        created_at=row.created_at,
    )
