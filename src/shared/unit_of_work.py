"""Unit-of-Work port + SQLAlchemy adapter (§7.8, NFR-TX1).

Application use cases open exactly one transaction per call:

    async with uow:
        await uow.bookings.add(booking)
        uow.collect(booking.pop_events())
        await uow.commit()
    # uow.commit() also flushes collected events through the EventBus
    # after the DB transaction commits.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import TracebackType
from typing import Protocol, Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.shared.events import DomainEvent, EventBus


class UnitOfWork(Protocol):
    """The interface application services depend on."""

    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    def collect(self, events: list[DomainEvent]) -> None: ...


class SqlAlchemyUnitOfWork:
    """Default UoW: one AsyncSession, one transaction, post-commit event dispatch."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        event_bus: EventBus,
    ) -> None:
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._session: AsyncSession | None = None
        self._pending_events: list[DomainEvent] = []

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork used outside `async with` block")
        return self._session

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        await self._session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            if exc is not None:
                await self.rollback()
            else:
                # If the caller forgot to commit, treat it as rollback rather
                # than silently persisting (safer default).
                if self._session is not None and self._session.in_transaction():
                    await self.rollback()
        finally:
            if self._session is not None:
                await self._session.close()
                self._session = None
            self._pending_events.clear()

    async def commit(self) -> None:
        await self.session.commit()
        # Dispatch only AFTER the DB has committed (NFR-EV1).
        if self._pending_events:
            await self._event_bus.publish_many(self._pending_events)
            self._pending_events.clear()

    async def rollback(self) -> None:
        await self.session.rollback()
        self._pending_events.clear()

    def collect(self, events: list[DomainEvent]) -> None:
        self._pending_events.extend(events)


@asynccontextmanager
async def transaction(uow: UnitOfWork) -> AsyncIterator[UnitOfWork]:
    """Convenience wrapper for `async with` use in application services."""
    async with uow:
        yield uow
        await uow.commit()
