"""HTTP middlewares (NFR-X5)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.logging import request_id_var
from src.shared.ids import new_id

REQUEST_ID_HEADER = "X-Request-Id"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Reads or generates `X-Request-Id`, stamps it on logs + responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = _parse_or_new(incoming)
        token = request_id_var.set(str(request_id))
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers[REQUEST_ID_HEADER] = str(request_id)
        return response


def _parse_or_new(value: str | None) -> UUID:
    if value:
        try:
            return UUID(value)
        except ValueError:
            pass
    return new_id()
