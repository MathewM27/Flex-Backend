"""Maps domain exceptions to the API error envelope (NFR-E2, NFR-E4).

Envelope shape (also documented in frontendRequirements.md §8.1):
    { "error": { "code": "BOOKING_OVERLAP", "message": "..." } }

The domain layer NEVER raises HTTPException — it only knows DomainError.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.logging import get_logger
from src.shared.errors import DomainError

logger = get_logger(__name__)


def _envelope(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    logger.info(
        "domain_error",
        code=exc.code,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=exc.http_status,
        content=_envelope(exc.code, exc.message),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Collapse pydantic's structured errors into a single human-readable
    # message; field-level error rendering is a frontend concern in v1.
    first = exc.errors()[0] if exc.errors() else {"msg": "Invalid request."}
    msg = str(first.get("msg", "Invalid request."))
    return JSONResponse(
        status_code=422,
        content=_envelope("VALIDATION_ERROR", msg),
    )


async def starlette_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(_status_code_to_label(exc.status_code), str(exc.detail)),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=500,
        content=_envelope("INTERNAL_ERROR", "Something went wrong."),
    )


def _status_code_to_label(code: int) -> str:
    return {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
    }.get(code, "ERROR")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
