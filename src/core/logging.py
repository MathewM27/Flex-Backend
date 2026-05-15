"""Structured JSON logging with request-id correlation (NFR-X5, NFR-O4).

Use `get_logger(__name__)` everywhere. Never use the stdlib root logger directly.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import MutableMapping
from contextvars import ContextVar
from typing import Any

import structlog

# Set by RequestIdMiddleware on every request; read by the structlog processor.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def _add_request_id(
    _: Any, __: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    request_id = request_id_var.get()
    if request_id is not None:
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    """Initializes structlog + stdlib logging once at process start."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _add_request_id,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)  # type: ignore[no-any-return]
