# 0004 — Event delivery: in-process synchronous

- **Status:** Accepted
- **Date:** 2026-05-15
- **Deciders:** Mathews Mwangi

## Context

The booking module needs to notify the notification module when a booking
is paid, accepted, declined, or cancelled. We want the modules decoupled
(notification is an adapter that can be swapped or removed), so this
goes through a domain event mechanism rather than direct service calls.

The question is *how* events are delivered:

1. **In-process synchronous** — handlers run in the same request after
   the DB commits.
2. **Outbox table + background worker** — events are written to a DB
   table in the same transaction; a worker picks them up and dispatches
   them. Guarantees at-least-once delivery, survives crashes.
3. **Direct service calls** — no abstraction, the booking service calls
   the notification service directly.

## Decision

**In-process synchronous dispatch after Unit-of-Work commit.**

- An `InProcessEventBus` adapter implements an `EventBus` port.
- Domain aggregates accumulate events; the application service hands
  them to the UoW; the UoW dispatches them on `commit()` (NFR-EV1).
- Handler failures are logged but **do not** roll back the originating
  transaction — the booking state is the source of truth, notifications
  are best-effort (NFR-N4, NFR-EV2).
- Publishers depend on the `EventBus` port only, not on any concrete
  dispatcher.

## Consequences

**Positive**

- Zero infrastructure: no worker, no extra container, no outbox table
  to manage.
- Tests can verify event flow without backgrounding anything (NFR-T7
  uses this).
- Failure isolation rule (handler crash ≠ booking rollback) matches
  the product semantics we want.

**Negative**

- **At-most-once** delivery. If the process dies between commit and the
  handler running, the notification is lost. Acceptable for v1: an SMS
  miss is annoying, not corrupting.
- Slow handlers extend request latency. Mitigated by handlers being
  thin (a single Twilio call); if we add a slow handler we move to
  outbox first.

## Migration trigger

Switch to **outbox + worker** when *any* of:

- We add a handler that performs work expensive enough to bother the
  user's request latency (>200ms p50).
- We need at-least-once delivery for any new event type (payouts,
  audit trails, invoicing).
- We start needing cross-process consumers (analytics service, etc.).

The migration is a new adapter + an `outbox` table + a worker entry
point in compose. Publishers don't change. This ADR will be superseded
by ADR-NNNN at that point.

## Alternatives considered

- **Outbox now.** Solves a problem we don't have yet, at a real
  operational cost. Premature.
- **Direct service calls.** Violates the modular-monolith contract
  (NFR-A2) and would force a refactor when the first cross-cutting
  concern (audit log, analytics) wants the same events.
