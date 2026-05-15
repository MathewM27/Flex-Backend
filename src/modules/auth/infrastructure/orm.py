"""SQLAlchemy ORM mapping for the auth module."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.modules.auth.domain.role import Role


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(72), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role, name="user_role"), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
