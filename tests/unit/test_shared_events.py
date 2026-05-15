"""In-process EventBus — NFR-EV1, NFR-EV2."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.shared.events import DomainEvent, InProcessEventBus


@dataclass(frozen=True, slots=True)
class ThingHappened(DomainEvent):
    value: int


@dataclass(frozen=True, slots=True)
class OtherThing(DomainEvent):
    note: str


@pytest.mark.asyncio
async def test_publish_invokes_subscribed_handler() -> None:
    bus = InProcessEventBus()
    received: list[ThingHappened] = []

    async def handler(event: ThingHappened) -> None:
        received.append(event)

    bus.subscribe(ThingHappened, handler)
    await bus.publish(ThingHappened(value=1))

    assert received == [ThingHappened(value=1)]


@pytest.mark.asyncio
async def test_publish_routes_only_to_matching_event_type() -> None:
    bus = InProcessEventBus()
    thing_calls = 0
    other_calls = 0

    async def on_thing(_: ThingHappened) -> None:
        nonlocal thing_calls
        thing_calls += 1

    async def on_other(_: OtherThing) -> None:
        nonlocal other_calls
        other_calls += 1

    bus.subscribe(ThingHappened, on_thing)
    bus.subscribe(OtherThing, on_other)
    await bus.publish(ThingHappened(value=1))

    assert (thing_calls, other_calls) == (1, 0)


@pytest.mark.asyncio
async def test_handler_failure_does_not_break_other_handlers() -> None:
    """NFR-EV2: a misbehaving subscriber must not poison the request."""
    bus = InProcessEventBus()
    second_called = False

    async def broken(_: ThingHappened) -> None:
        raise RuntimeError("boom")

    async def healthy(_: ThingHappened) -> None:
        nonlocal second_called
        second_called = True

    bus.subscribe(ThingHappened, broken)
    bus.subscribe(ThingHappened, healthy)

    await bus.publish(ThingHappened(value=1))  # must not raise

    assert second_called is True
