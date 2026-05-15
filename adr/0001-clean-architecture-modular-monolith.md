# 0001 — Clean architecture modular monolith

- **Status:** Accepted
- **Date:** 2026-05-15
- **Deciders:** Mathews Mwangi

## Context

We are building a small but production-shaped booking backend with a known
set of bounded contexts (auth, property, booking, payment, notification)
and an explicit non-goal of immediate horizontal scale. We also know that
some of these contexts (payment, notification) will be swapped to real
external providers within months.

Two competing pressures:

1. **Decoupling**: payment/notification adapters must be swappable without
   touching the rest of the system; the booking state machine must not
   know about HTTP or SQL.
2. **Operational simplicity**: a small team should be able to run the whole
   thing with `docker compose up` and reason about it linearly.

## Decision

Adopt a **modular monolith** organized internally by **Clean Architecture**:

- One deployable FastAPI application.
- One Python process at runtime.
- Inside `src/modules/`, each bounded context is its own module with the
  four-layer split: `domain/`, `application/`, `infrastructure/`,
  `interfaces/`.
- Dependencies point inward only. Domain depends on nothing; application
  depends on domain ports; infrastructure and interfaces depend inward.
- Cross-module communication happens through application services or
  domain events — never direct table joins.

## Consequences

**Positive**

- Swapping a payment or notification provider is a new adapter, not a
  refactor (validated by FR-PAY1 / FR-N1 needing this anyway).
- Tests can target the domain in isolation; the bulk of the suite needs
  no DB or network (NFR-T1).
- Splitting a module into its own service later is mechanical, not a
  re-architecture.

**Negative / trade-offs**

- More files than a "throw everything in `models.py`" Django/Flask layout.
  New contributors will need the orientation in [requirements.md §7.1–§7.10]
  and the per-module `docs.md` files.
- Some indirection (ports + adapters) feels heavy for trivial CRUD. We
  accept this cost because the *non*-trivial pieces (booking state
  machine, payment webhook, event-driven notifications) are exactly
  where Clean Architecture pays off.

## Alternatives considered

- **Flat Django/Flask-style layout.** Simpler today, but the booking ↔
  payment ↔ notification coupling we know is coming would force a
  rewrite within a quarter.
- **Microservices from day one.** Operationally heavy for a team this
  size and not justified by the load profile we expect.
