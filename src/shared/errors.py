"""Domain exception hierarchy (NFR-E1).

Every error code in the system is declared exactly once in this file
(NFR-E5). HTTP mapping lives in `src/api/exception_handlers.py`; the
domain layer never raises `HTTPException`.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base for all domain-level errors. Subclasses set `code`."""

    code: str = "DOMAIN_ERROR"
    http_status: int = 400

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code

    def __str__(self) -> str:  # pragma: no cover — trivial
        return f"[{self.code}] {self.message}"


class NotFoundError(DomainError):
    code = "NOT_FOUND"
    http_status = 404


class ConflictError(DomainError):
    code = "CONFLICT"
    http_status = 409


class ValidationError(DomainError):
    code = "VALIDATION_ERROR"
    http_status = 422


class ForbiddenError(DomainError):
    code = "FORBIDDEN"
    http_status = 403


class UnauthorizedError(DomainError):
    code = "UNAUTHORIZED"
    http_status = 401


class ExternalServiceError(DomainError):
    code = "EXTERNAL_SERVICE_ERROR"
    http_status = 502
