"""FastAPI router for auth endpoints (FR-A1 - FR-A6)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.auth.application.use_cases import (
    LoginUser,
    LoginUserCommand,
    SignupUser,
    SignupUserCommand,
)
from src.modules.auth.domain.entities import User
from src.modules.auth.interfaces.dependencies import (
    get_current_user,
    get_login_use_case,
    get_signup_use_case,
)
from src.modules.auth.interfaces.schemas import (
    LoginRequest,
    SignupRequest,
    SignupResponse,
    TokenResponse,
    UserResponse,
)
from src.shared.errors import ConflictError, UnauthorizedError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    body: SignupRequest,
    use_case: Annotated[SignupUser, Depends(get_signup_use_case)],
) -> SignupResponse:
    try:
        user_id = await use_case.execute(
            SignupUserCommand(
                email=body.email,
                password=body.password,
                full_name=body.full_name,
                role=body.role,
                phone=body.phone,
            )
        )
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return SignupResponse(
        id=user_id,
        email=body.email,
        full_name=body.full_name,
        role=body.role,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    use_case: Annotated[LoginUser, Depends(get_login_use_case)],
) -> TokenResponse:
    try:
        token = await use_case.execute(LoginUserCommand(email=body.email, password=body.password))
    except UnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email.value,
        full_name=current_user.full_name,
        role=current_user.role,
        phone=current_user.phone,
    )
