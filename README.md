# Flex-Backend

A small production-shaped backend for a short-stay booking service (Airbnb-like).
Built with **FastAPI + PostgreSQL**, containerized with Docker, organized around
**Clean Architecture / DDD** so individual concerns (auth, properties, bookings,
payments, notifications) can be evolved independently and infrastructure
adapters (Stripe, PayPal, S3, SendGrid, Prometheus, …) can be plugged in later
without touching the domain.

The frontend is a separate repository — two Next.js apps share one Next codebase
behind a role switch (landlord dashboard + tenant marketplace) and consume this
API.

---

## Status

Pre-implementation. This repo currently contains the agreed
[requirements](requirements.md) and this README. Code scaffolding is the next
step.

---

## Stack

| Layer            | Choice                                               |
| ---------------- | ---------------------------------------------------- |
| API framework    | FastAPI (async)                                      |
| Language         | Python 3.12                                          |
| Dependency mgmt  | uv (Astral) — `uv.lock` committed                    |
| DB               | PostgreSQL 16                                        |
| ORM / migrations | SQLAlchemy 2.x (async) + Alembic                     |
| Auth             | JWT access token (single token, no refresh) + bcrypt |
| Validation       | Pydantic v2                                          |
| Notifications    | Twilio (SMS sandbox) behind a provider interface     |
| Payments         | Mock provider behind a provider interface            |
| Container        | Docker + docker-compose                              |
| Tests            | pytest + httpx (unit / integration / e2e)            |
| CI               | GitHub Actions (lint, typecheck, test, migrations)   |
| Commits          | Conventional Commits + pre-commit hooks              |

---

## High-level architecture

The codebase is a **modular monolith**. Each business capability is a
**bounded context** (module) with its own internal Clean Architecture layers:

```text
src/
├── modules/
│   ├── auth/              # signup, login, JWT issuing, password hashing
│   ├── property/          # landlord property CRUD + tenant listing/filter
│   ├── booking/           # booking lifecycle, calendar / availability
│   ├── payment/           # payment intent, mock provider, webhook handler
│   └── notification/      # SMS dispatch via Twilio (provider-agnostic)
├── shared/                # cross-cutting: errors, base types, ids, time
├── core/                  # config, db engine, security primitives, DI wiring
└── api/                   # FastAPI app, routers, dependency injection, middleware
```

Inside every module:

```text
modules/<context>/
├── domain/         # entities, value objects, domain events, repository PORTS
├── application/    # use cases / services — orchestrate domain + ports
├── infrastructure/ # adapters: SQLAlchemy repositories, Twilio client, mock-payment
├── interfaces/     # FastAPI router + request/response schemas (DTOs)
└── docs.md         # short explanation of what this module owns
```

### Key principles

- **Dependencies point inward.** `domain` knows nothing about FastAPI,
  SQLAlchemy, or Twilio. `application` depends only on `domain` (ports).
  `infrastructure` and `interfaces` depend inward.
- **Ports & adapters.** External systems (DB, Twilio, payment provider) are
  hidden behind interfaces declared in `domain`. Swapping Twilio for SNS, or
  the mock payment provider for Stripe, is a new adapter — no domain changes.
- **One module owns its tables.** Cross-module communication goes through
  application services or domain events, not direct table joins.
- **Webhooks for async state transitions.** Payment confirmation arrives via a
  webhook endpoint (even from the mock provider) so the real-provider swap is a
  config change, not a refactor.

---

## Booking flow (agreed)

```text
Tenant picks dates ─▶ POST /bookings (creates booking, status=PENDING_PAYMENT)
                  ─▶ POST /payments/intent (mock intent created)
                  ─▶ Tenant "pays" on frontend
                  ─▶ Mock provider posts webhook ─▶ booking=PENDING_APPROVAL
                                                ─▶ SMS to landlord
Landlord accepts ─▶ booking=CONFIRMED  ─▶ SMS to tenant
Landlord declines ─▶ booking=DECLINED ─▶ mock refund ─▶ SMS to tenant
Landlord cancels later ─▶ booking=CANCELLED ─▶ mock refund ─▶ SMS to tenant
Tenant cancels ─▶ booking=CANCELLED ─▶ no refund (for now)
```

Full state machine and rules: see [requirements.md](requirements.md).

---

## Running locally

> Docker Desktop is required. Nothing else is.

```bash
# 1. Copy env template
cp .env.example .env

# 2. Bring up Postgres + API
docker compose up --build

# 3. Run migrations (in another terminal)
docker compose exec api alembic upgrade head

# 4. Visit the docs
open http://localhost:8000/api/v1/docs
```

> The Twilio sandbox and JWT secret values in `.env.example` are placeholders.
> Provide your own before the relevant flows will work.

---

## Testing & CI

The project is built **test-first (TDD)**. See [requirements.md §11](requirements.md)
for the loop and [§7.4](requirements.md) for the test taxonomy.

```bash
# All tests with coverage (same command CI runs)
docker compose exec api pytest --cov=src --cov-fail-under=80

# Just the fast unit tests during a TDD loop
docker compose exec api pytest tests/unit -q
```

CI runs on every push and PR via [`.github/workflows/ci.yml`](.github/workflows/ci.yml):

- `lint` — `ruff check` + `ruff format --check`
- `typecheck` — `mypy` (strict on domain + application)
- `test` — unit + integration + e2e against a Postgres 16 service container, with coverage floor
- `migrations-check` — `alembic upgrade head` from zero + `alembic check` (no drift)

`main` is branch-protected; the four jobs above must pass before merge.

---

## Project layout (target)

```text
.
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── alembic.ini
├── alembic/                # migrations
├── .env.example
├── src/
│   ├── main.py             # FastAPI app factory
│   ├── api/
│   ├── core/
│   ├── shared/
│   └── modules/
│       ├── auth/
│       ├── property/
│       ├── booking/
│       ├── payment/
│       └── notification/
├── tests/
├── README.md
└── requirements.md
```

Every folder under `src/modules/` carries a short `docs.md` explaining what it
owns and why.

---

## What is intentionally **not** in scope yet

These will fit into the existing structure later without redesign:

- Real payment integration (Stripe / PayPal adapter)
- Image upload + object storage (S3 / MinIO) — for now properties just store
  image URLs supplied by the landlord
- Email + in-app notifications (only SMS via Twilio sandbox for now)
- Refresh tokens, OAuth, MFA
- Admin role, multi-tenancy beyond the landlord/tenant split
- Observability (Prometheus, OpenTelemetry, structured log shipping)
- Rate limiting / WAF
- Cancellation policies configurable per property
- Reviews, messaging, search ranking

---

## License

TBD.
