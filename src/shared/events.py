"""In-process domain event bus (§7.8, NFR-EV1).

Events fire **after** the Unit of Work commits, synchronously, on the
same request. Handler failures are logged but never roll back the
originating transaction (NFR-EV2).

When the time comes to move to an outbox + worker, this module is the
only adapter that changes; publishers depend on the `EventBus` port.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Base for all domain events. Subclasses are also frozen dataclasses."""


E = TypeVar("E", bound=DomainEvent)
Handler = Callable[[E], Awaitable[None]]


class EventBus(Protocol):
    def subscribe(self, event_type: type[DomainEvent], handler: Handler[Any]) -> None: ...
    async def publish(self, event: DomainEvent) -> None: ...
    async def publish_many(self, events: list[DomainEvent]) -> None: ...


class InProcessEventBus:
    """Sync, in-process dispatcher. Handlers run sequentially.

    Failures in any handler are logged but do not propagate, so one
    misbehaving subscriber cannot poison the request.
    """

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[Handler[Any]]] = {}

    def subscribe(self, event_type: type[DomainEvent], handler: Handler[Any]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(type(event), []):
            try:
                await handler(event)
            except Exception:
                logger.exception(
                    "event_handler_failed",
                    event_type=type(event).__name__,
                    handler=getattr(handler, "__qualname__", repr(handler)),
                )

    async def publish_many(self, events: list[DomainEvent]) -> None:
        for event in events:
            await self.publish(event)
