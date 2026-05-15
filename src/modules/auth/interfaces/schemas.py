"""Pydantic request/response schemas for auth endpoints."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator

from src.modules.auth.domain.role import Role


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Role
    phone: str

    @field_validator("password")
    @classmethod
    def _min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v


class SignupResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: Role
    phone: str
