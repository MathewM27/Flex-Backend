# Flex-Backend — Requirements

This document captures the agreed scope, domain model, API surface, and design
decisions for the first iteration of the backend. It is the source of truth the
[README](README.md) is built on.

> Anything not listed here is **out of scope** for v1. Items in
> "Out of scope (later)" are intentionally deferred but must fit into the
> agreed architecture without redesign.

---

## 1. Goals

- Ship a small but production-shaped backend for a short-stay booking service.
- Cleanly decouple domain from infrastructure so payment providers, storage,
  notification channels, and observability tooling can be swapped/added later.
- Be deployable on a single host via `docker compose` with PostgreSQL.
- Expose a stable HTTP API (`/api/v1/…`) consumable by a separate Next.js
  frontend repo serving both landlord and tenant views.

## 2. Non-goals (v1)

- Real money movement. Payments are a mock provider behind the same interface
  Stripe would implement.
- File uploads / object storage. Properties carry image URLs only.
- Email, push, or in-app notifications. SMS via Twilio sandbox only.
- Refresh tokens, OAuth, social login, MFA.
- Admin role, organizations, teams, sub-accounts.
- Reviews, messaging, search ranking, recommendations.
- Observability stack (Prometheus, OTel). Hooks must be feasible to add later.

---

## 3. Actors and roles

| Role       | Description                                                          |
| ---------- | -------------------------------------------------------------------- |
| `TENANT`   | Books properties. Pays. Can cancel (no refund in v1).                |
| `LANDLORD` | Creates and manages properties. Accepts/declines/cancels bookings.   |

A user has exactly one role, chosen at signup. No role switching in v1.

---

## 4. Functional requirements

### 4.1 Auth (module: `auth`)

- **FR-A1** A user can sign up with `email`, `password`, `full_name`, `role`
  (`TENANT` | `LANDLORD`), and `phone_number` (E.164; required because we use
  SMS).
- **FR-A2** Passwords are hashed with bcrypt. Plaintext is never stored or
  logged.
- **FR-A3** A user can log in with email + password and receives a JWT access
  token (single token, no refresh). Token contains `sub` (user id), `role`,
  `exp`. Default TTL: 24h (configurable).
- **FR-A4** Protected endpoints require `Authorization: Bearer <token>`.
- **FR-A5** Role-based authorization: landlord-only endpoints reject tenants
  with `403`, and vice-versa.
- **FR-A6** `GET /api/v1/auth/me` returns the current user.

### 4.2 Properties (module: `property`)

- **FR-P1** A landlord can create a property with: `title`, `description`,
  `city`, `country`, `address`, `price_per_night` (decimal), `currency`
  (default `USD`), `max_guests`, `bedrooms`, `bathrooms`, `amenities` (list of
  strings), `image_urls` (list of URL strings).
- **FR-P2** A landlord can update or delete their own properties only.
- **FR-P3** A landlord can list their own properties (dashboard view).
- **FR-P4** Tenants can list all properties with filters:
  - by `city` (substring/ILIKE match)
  - by `min_price` / `max_price`
  - by `guests` (minimum capacity)
  - by `check_in` + `check_out` — excludes properties with any
    `CONFIRMED` or `PENDING_APPROVAL` booking overlapping the requested window.
- **FR-P5** Anyone (authenticated) can view a property detail by id, including
  a calendar of unavailable date ranges for the next N months (default 6).
- **FR-P6** Image handling is URL-only in v1. The backend validates URL syntax
  but does not fetch or host the image.

### 4.3 Bookings (module: `booking`)

#### State machine

```text
            ┌─────────────────────┐
            │   PENDING_PAYMENT   │  (created by tenant; no money yet)
            └──────────┬──────────┘
        payment.succeeded webhook
                       │
            ┌──────────▼──────────┐
            │  PENDING_APPROVAL   │  (paid; landlord must decide)
            └──────────┬──────────┘
        ┌──────────────┼──────────────────┐
        │              │                  │
landlord accepts  landlord declines   tenant cancels
        │              │                  │
        ▼              ▼                  ▼
   CONFIRMED       DECLINED           CANCELLED
                  (refund)            (no refund)
        │
landlord cancels later
        │
        ▼
   CANCELLED  ← when triggered by landlord, refund issued
```

Plus terminal `EXPIRED` for `PENDING_PAYMENT` bookings that aren't paid within
a configurable timeout (default 15 min) — releases the date hold.

#### Rules

- **FR-B1** A tenant creates a booking with `property_id`, `check_in`,
  `check_out`, `guest_count`, optional `guest_notes`. The server computes
  `nights` and `total_amount = nights * property.price_per_night`.
- **FR-B2** `check_in < check_out`, both in the future, `guest_count ≤
  property.max_guests`.
- **FR-B3** Overlap check at creation: reject if any existing booking for the
  same property in `[PENDING_PAYMENT, PENDING_APPROVAL, CONFIRMED]` overlaps
  the requested range. The overlap check runs in a single transaction with the
  insert to avoid races.
- **FR-B4** Landlord sees all bookings for their properties; tenant sees only
  their own bookings.
- **FR-B5** Landlord can `accept` a booking only when status is
  `PENDING_APPROVAL` → moves to `CONFIRMED`. SMS to tenant.
- **FR-B6** Landlord can `decline` a booking only when status is
  `PENDING_APPROVAL` → moves to `DECLINED`, issues a full refund via the
  payment provider, SMS to tenant.
- **FR-B7** Landlord can `cancel` a `CONFIRMED` booking → `CANCELLED`, full
  refund, SMS to tenant.
- **FR-B8** Tenant can `cancel` a booking in `PENDING_PAYMENT`,
  `PENDING_APPROVAL`, or `CONFIRMED` → `CANCELLED`. **No refund in v1** even
  if already paid (per agreed policy). SMS to landlord.
- **FR-B9** All status transitions emit a domain event consumed by the
  notification module.

### 4.4 Payments (module: `payment`)

The payment module is intentionally generic. v1 ships a `MockPaymentProvider`;
a real provider (Stripe/PayPal) is a future adapter implementing the same port.

#### Port (interface)

```python
class PaymentProvider(Protocol):
    async def create_intent(self, *, amount: Decimal, currency: str,
                            booking_id: UUID, metadata: dict) -> PaymentIntent: ...
    async def refund(self, *, payment_id: UUID, amount: Decimal) -> Refund: ...
    def verify_webhook(self, *, raw_body: bytes, signature: str) -> WebhookEvent: ...
```

#### Payment rules

- **FR-PAY1** `POST /api/v1/payments/intent` (tenant) creates a payment intent
  for a `PENDING_PAYMENT` booking. Response includes a `client_secret` (mock
  value in v1; same field name Stripe uses so frontend code doesn't change).
- **FR-PAY2** Frontend simulates payment success and triggers
  `POST /api/v1/payments/mock/confirm` which makes the mock provider post a
  webhook to the backend with a valid signature. **The booking is only
  considered paid when the webhook arrives**, never on the confirm response.
  This forces the codebase to handle the same async path Stripe uses.
- **FR-PAY3** `POST /api/v1/payments/webhook` is the single webhook endpoint.
  It verifies the signature, looks up the intent, transitions the booking
  `PENDING_PAYMENT → PENDING_APPROVAL`, persists a `Payment` record, and emits
  `BookingPaid` event.
- **FR-PAY4** Webhook handling is **idempotent** keyed on the provider event
  id. Replays must not double-transition state.
- **FR-PAY5** Refunds are issued only by the system (never by direct API call)
  in response to landlord decline / landlord cancel. The refund call goes
  through the same provider port; the mock provider always succeeds.
- **FR-PAY6** Booking total, payment amount, and refund amount are stored with
  the booking & payment records for auditability.

### 4.5 Notifications (module: `notification`)

#### Port

```python
class NotificationSender(Protocol):
    async def send_sms(self, *, to: str, body: str,
                       template_key: str, context: dict) -> NotificationResult: ...
```

#### Notification rules

- **FR-N1** v1 ships a `TwilioSmsSender` adapter using the Twilio sandbox.
- **FR-N2** A `ConsoleSmsSender` adapter exists for local dev / tests (no
  network calls). Selected by env (`NOTIFICATION_PROVIDER=console|twilio`).
- **FR-N3** Triggers (driven by domain events):
  - `BookingPaid` → SMS to landlord ("new booking awaiting approval")
  - `BookingAccepted` → SMS to tenant
  - `BookingDeclined` → SMS to tenant ("declined; refund issued")
  - `BookingCancelledByLandlord` → SMS to tenant ("cancelled; refund issued")
  - `BookingCancelledByTenant` → SMS to landlord
- **FR-N4** Every send attempt is persisted (status, provider id, error if
  any). Failures are logged but **do not** roll back the booking transition —
  the booking state is the source of truth, notifications are best-effort.

---

## 5. Domain model (summary)

```text
User           (id, email[unique], password_hash, full_name, role, phone, created_at)
Property       (id, landlord_id→User, title, description, city, country, address,
                price_per_night, currency, max_guests, bedrooms, bathrooms,
                amenities[json], image_urls[json], created_at, updated_at)
Booking        (id, property_id→Property, tenant_id→User, check_in, check_out,
                nights, guest_count, guest_notes, total_amount, currency,
                status, created_at, updated_at)
Payment        (id, booking_id→Booking, provider, provider_intent_id,
                provider_event_id, amount, currency, status, created_at)
Refund         (id, payment_id→Payment, provider_refund_id, amount, status, created_at)
Notification   (id, user_id→User, channel, template_key, body, status,
                provider_message_id, error, created_at)
```

Indexes worth noting:

- `bookings (property_id, status, check_in, check_out)` for overlap queries.
- `payments (provider_event_id) unique` for webhook idempotency.
- `users (email) unique citext`.

---

## 6. API surface (v1)

All under `/api/v1`. JSON request & response. Auth via `Bearer` token unless
marked Public.

### Auth

| Method | Path             | Who    | Purpose                |
| ------ | ---------------- | ------ | ---------------------- |
| POST   | `/auth/signup`   | Public | Create account         |
| POST   | `/auth/login`    | Public | Get JWT                |
| GET    | `/auth/me`       | Any    | Current user           |

### Properties

| Method | Path                       | Who      | Purpose                                       |
| ------ | -------------------------- | -------- | --------------------------------------------- |
| GET    | `/properties`              | Any      | List + filter (city, price, guests, dates)    |
| GET    | `/properties/{id}`         | Any      | Detail + unavailable date ranges              |
| POST   | `/properties`              | Landlord | Create                                        |
| PATCH  | `/properties/{id}`         | Landlord | Update own                                    |
| DELETE | `/properties/{id}`         | Landlord | Delete own                                    |
| GET    | `/properties/mine`         | Landlord | List own (dashboard)                          |

### Bookings

| Method | Path                                  | Who      | Purpose                              |
| ------ | ------------------------------------- | -------- | ------------------------------------ |
| POST   | `/bookings`                           | Tenant   | Create booking (PENDING_PAYMENT)     |
| GET    | `/bookings/mine`                      | Tenant   | List own bookings                    |
| GET    | `/bookings/received`                  | Landlord | List bookings on landlord's props    |
| GET    | `/bookings/{id}`                      | Both     | Detail (must own one side)           |
| POST   | `/bookings/{id}/accept`               | Landlord | PENDING_APPROVAL → CONFIRMED         |
| POST   | `/bookings/{id}/decline`              | Landlord | PENDING_APPROVAL → DECLINED + refund |
| POST   | `/bookings/{id}/cancel`               | Both     | Role-dependent rules per FR-B7/B8    |

### Payments

| Method | Path                             | Who      | Purpose                              |
| ------ | -------------------------------- | -------- | ------------------------------------ |
| POST   | `/payments/intent`               | Tenant   | Create intent for own booking        |
| POST   | `/payments/mock/confirm`         | Tenant   | Dev-only: tells mock to fire webhook |
| POST   | `/payments/webhook`              | Provider | Webhook (signature-verified)         |
| GET    | `/payments/booking/{booking_id}` | Both     | Payment + refund history             |

### Health

| Method | Path        | Who    | Purpose                       |
| ------ | ----------- | ------ | ----------------------------- |
| GET    | `/health`   | Public | Liveness                      |
| GET    | `/ready`    | Public | Readiness (DB ping)           |

OpenAPI/Swagger is auto-served at `/api/v1/docs`.

---

## 7. Non-functional requirements

### 7.1 Security (minimal but real)

- **NFR-S1** Passwords bcrypt-hashed, cost ≥ 12.
- **NFR-S2** JWT signed with HS256 using a secret loaded from env. The secret
  is required at startup; the app refuses to boot without it.
- **NFR-S3** All endpoints except auth + webhook + health require JWT.
- **NFR-S4** CORS is allowlist-based, configured via env
  (`CORS_ORIGINS=https://landlord.app,https://tenant.app`). No wildcard in
  prod.
- **NFR-S5** Input validation via Pydantic on every request body and query
  param. Reject unknown fields.
- **NFR-S6** Webhook endpoint verifies provider signature on every call.
- **NFR-S7** Sensitive values (JWT secret, Twilio token, DB password) are
  loaded from env only — never committed. `.env.example` ships placeholders.
- **NFR-S8** Standard FastAPI security headers middleware (HSTS,
  X-Content-Type-Options, frame deny). Rate-limiting is **out of scope** but
  middleware slot must exist so it can be added without touching handlers.

### 7.2 Architecture

- **NFR-A1** Clean Architecture / DDD. Domain depends on nothing. Application
  depends on domain. Infrastructure and interfaces depend inward.
- **NFR-A2** Each module owns its tables. No cross-module direct table
  joins — go through application services or events.
- **NFR-A3** Dependency injection at the FastAPI router boundary. No global
  singletons inside the domain or application layers.
- **NFR-A4** All external integrations (DB, Twilio, payments) sit behind ports
  in the domain layer; concrete adapters live in `infrastructure/`.
- **NFR-A5** Domain events are an in-process pub/sub today; swappable to a
  real broker later without changing publishers.

### 7.3 Operability

- **NFR-O1** Runs locally with `docker compose up`. Postgres data persists in
  a named volume.
- **NFR-O2** All config via env, parsed at startup with `pydantic-settings`.
  Missing required env aborts startup.
- **NFR-O3** Alembic migrations only — no `create_all` at runtime.
- **NFR-O4** Logs are structured (JSON) so a log shipper can be added later
  without code changes.
- **NFR-O5** `GET /health` and `GET /ready` exist from day one.

### 7.4 Testing

The project is built **test-first (TDD)** for the domain and application
layers. See §11 for the development loop.

- **NFR-T1** `pytest` set up with three layers, each in its own folder:
  - `tests/unit/` — domain + application use cases. **No DB, no network.**
    Use in-memory fakes for every port (`InMemoryBookingRepository`,
    `FakeNotificationSender`, `FakePaymentProvider`). These tests must run
    in well under one second each and form the bulk of the suite.
  - `tests/integration/` — adapters against real infrastructure: SQLAlchemy
    repositories against a disposable Postgres, the mock payment provider's
    webhook signing/verification round-trip, the console notification sender.
  - `tests/e2e/` — full HTTP surface via `httpx.AsyncClient` against the
    FastAPI app, with a disposable Postgres and the console + mock adapters
    wired in. One happy-path end-to-end test of
    `signup → create property → book → mock-pay → webhook → landlord accept
    → notifications recorded` is **mandatory** (smoke test for the whole
    stack).
- **NFR-T2** Test data is built with **factory functions** (one per
  aggregate: `make_user`, `make_property`, `make_booking`) living in
  `tests/factories/`. No fixtures-as-test-data; factories keep tests
  readable and intent-revealing.
- **NFR-T3** Each module's domain + application code must reach **≥ 90%
  line coverage**. Overall project floor is **≥ 80%**. Infrastructure and
  interface layers have no hard coverage floor — they're exercised by
  integration/e2e tests. Coverage is measured with `coverage.py` and the
  thresholds are enforced in CI.
- **NFR-T4** Tests run against the same Postgres major version used in
  production (Postgres 16). SQLite is **never** used as a test substitute —
  it would silently mask Postgres-specific behavior (ILIKE, JSONB, partial
  indexes, transactional DDL).
- **NFR-T5** A `conftest.py` provides per-test transactional rollback so
  integration and e2e tests share a single Postgres container and don't
  truncate between cases. Each test runs inside a SAVEPOINT that is rolled
  back on teardown.
- **NFR-T6** Tests must be deterministic — no real time, no real randomness.
  A `Clock` port returns "now"; tests inject a `FixedClock`. A `UUIDFactory`
  port produces deterministic ids in tests.
- **NFR-T7** Webhook idempotency (FR-PAY4) is a named test case, not an
  afterthought: replay the same provider event id twice; assert the booking
  transitions exactly once.

### 7.5 CI/CD

GitHub Actions is the v1 CI. The workflow lives at
`.github/workflows/ci.yml` and runs on every push and every pull request
targeting `main`.

#### Pipeline stages

All stages run in parallel where possible. The whole pipeline should
complete in **under 5 minutes** on a fresh cache.

1. **lint** — `ruff check .` and `ruff format --check .`
2. **typecheck** — `mypy src/` with `--strict` on `src/modules/*/domain` and
   `src/modules/*/application` (relaxed elsewhere to start).
3. **test** — runs unit + integration + e2e against a Postgres 16 **service
   container**. Steps:
   - Spin up Postgres 16 as a GitHub Actions service.
   - `alembic upgrade head` against it (this is itself a test: migrations
     must apply cleanly from zero).
   - `pytest --cov=src --cov-report=xml --cov-fail-under=80`.
   - Upload `coverage.xml` as a build artifact.
4. **migrations-check** — runs `alembic upgrade head` then
   `alembic check` (autogenerate diff is empty). Fails if models and
   migrations have drifted. Independent job so the failure is obvious.
5. **docker-build** *(on `main` only)* — builds the production image to
   confirm the Dockerfile still works. Not pushed anywhere in v1.

#### Conventions

- **NFR-CI1** Workflow uses `actions/setup-python@v5` with Python 3.12 and
  pip caching keyed on `pyproject.toml` / `uv.lock` (if using uv).
- **NFR-CI2** No production secrets are needed in CI for v1 — Twilio and
  payments are mocked via the `console` and `mock` adapters. CI sets
  `NOTIFICATION_PROVIDER=console`, `PAYMENT_PROVIDER=mock`, and a dummy
  `JWT_SECRET` and `PAYMENT_WEBHOOK_SECRET`.
- **NFR-CI3** Branch protection on `main`: PRs require `lint`, `typecheck`,
  `test`, and `migrations-check` to be green before merge. Linear history
  preferred; squash-merge is fine.
- **NFR-CI4** A `pre-commit` config mirrors a **subset** of CI locally
  (`ruff`, `ruff-format`, basic file hygiene). It is optional for
  contributors but recommended in the README.
- **NFR-CI5** CI failure output must be readable: pytest runs with `-ra` so
  short summaries of failures appear at the end, and coverage gaps are
  printed inline (`--cov-report=term-missing:skip-covered`).
- **NFR-CI6** A CD step (build + push image to a registry, deploy) is
  **out of scope for v1** but the `docker-build` job is the placeholder.
  When CD is added, it gets its own workflow file (`.github/workflows/cd.yml`)
  triggered on tags, not pushes — separating concerns now keeps the v1
  workflow simple.

### 7.6 Cross-cutting conventions

These are boundary policies that get inconsistent if every module
re-decides them. Locked once, here.

- **NFR-X1 IDs.** All primary keys are **UUIDv7** (time-ordered, B-tree
  friendly, sortable). Generated via a `UUIDFactory` port so tests can
  inject deterministic values. Never use database-generated integer ids.
- **NFR-X2 Time.** All datetimes stored and transmitted are **UTC,
  timezone-aware** (`datetime` with `tzinfo`). Naive `datetime` is
  **forbidden** at every layer; a runtime check in `shared/time.py`
  refuses naive values. API serializes ISO 8601 with the trailing `Z`.
  "Now" is read from a `Clock` port — never `datetime.now()` directly.
- **NFR-X3 Money.** Money is `Decimal` paired with an ISO 4217 currency
  code in a `Money` value object. Mixed-currency arithmetic raises
  `CurrencyMismatch`. Persisted as `numeric(12, 2)` + a `currency`
  column. Serialized as decimal strings (`"129.00"`). `float` is
  forbidden anywhere near money.
- **NFR-X4 Pagination.** Every list endpoint returns the same envelope:

  ```json
  { "items": [...], "total": 123, "limit": 20, "offset": 0 }
  ```

  Default `limit=20`, max `limit=100`. Codified in a
  `shared/pagination.py` `Page[T]` generic so handlers can't diverge.
- **NFR-X5 Request correlation.** A `RequestIdMiddleware` reads the
  `X-Request-Id` header (or generates a UUIDv7 if absent) and stores it
  in a `contextvars.ContextVar`. Every log record includes it
  automatically via a `logging.Filter`. The response echoes the same
  header back. Cannot be retrofitted cleanly — must exist from the
  first request.
- **NFR-X6 API versioning policy.** Path-based versioning under
  `/api/v{n}`. Breaking changes cut a new version; the previous version
  stays live for one minor release before removal. Non-breaking
  additions (new optional fields, new endpoints) ship under the
  existing version. v1 has no deprecation policy yet — recorded as
  ADR-0004 when it does.

### 7.7 Error handling

- **NFR-E1** A single domain exception hierarchy in `shared/errors.py`:

  ```text
  DomainError                     # base; abstract
   ├── NotFoundError              → 404
   ├── ConflictError              → 409   (e.g. BOOKING_OVERLAP)
   ├── ValidationError            → 422
   ├── ForbiddenError             → 403
   ├── UnauthorizedError          → 401
   └── ExternalServiceError       → 502   (Twilio down, payment provider down)
  ```

  Each subclass carries `code: str` (machine-readable, SCREAMING_SNAKE)
  and `message: str` (human-readable). Modules **extend** these — they
  don't invent parallel hierarchies.
- **NFR-E2** A single FastAPI exception handler maps every
  `DomainError` to the envelope:

  ```json
  { "error": { "code": "BOOKING_OVERLAP", "message": "Those dates are not available." } }
  ```

  This is the contract the [frontend](frontendRequirements.md) consumes.
- **NFR-E3** The **domain layer never raises `HTTPException`**. HTTP is
  an interface concern; the domain only knows `DomainError`.
- **NFR-E4** Unhandled exceptions are caught by a fallback handler that
  logs the full traceback **with the request id** and returns
  `{ "error": { "code": "INTERNAL_ERROR", "message": "Something went wrong." } }`
  with status 500. Stack traces are never returned to the client.
- **NFR-E5** Every error code is documented exactly once, in
  `shared/errors.py` next to the class that raises it.

### 7.8 Transactions & domain events

- **NFR-TX1 Unit of Work.** The application layer opens **one
  transaction per use-case call** via a `UnitOfWork` port. The
  SQLAlchemy adapter wraps an async session; commit happens at the end
  of the use case, rollback on any exception. Routers (interface
  layer) **never** open transactions directly.
- **NFR-TX2** The booking overlap check (FR-B3) and the booking insert
  happen inside the same UoW. The overlap query uses
  `SELECT … FOR UPDATE` on the property row (or a serializable
  transaction; pick one in the booking module's `docs.md`) to prevent
  the well-known double-book race.
- **NFR-EV1 Domain events.** Events are dispatched **in-process,
  synchronously, after the UoW commits**. An `EventBus` port exposes
  `publish(event)` and `subscribe(event_type, handler)`; the
  application service collects events on the aggregate and publishes
  them post-commit. Handlers run on the same request.
- **NFR-EV2 Failure isolation.** If a handler (e.g. SMS send) fails,
  the failure is logged with the request id but **does not** roll back
  the originating transaction — the booking transition is the source
  of truth, notifications are best-effort (matches FR-N4).
- **NFR-EV3 Future-proofing.** Publishers depend on the `EventBus`
  port only. Swapping in an outbox table + worker later is a new
  adapter, not a domain change. Recorded as deferred work in §9.

### 7.9 DTO ↔ domain boundary

- **NFR-D1** Pydantic schemas (request and response DTOs) live in
  `modules/<x>/interfaces/schemas.py`. Domain entities **never** appear
  in HTTP responses or accept HTTP payloads.
- **NFR-D2** Each module exposes a `to_response(entity) -> ResponseSchema`
  function in `interfaces/mappers.py`. Mapping is the single point
  where renaming a domain field decides whether the API changes.
- **NFR-D3** Request schemas validate input and pass **plain data**
  (primitives, dataclasses, value objects) into use cases. Use cases
  never accept Pydantic models — that would couple application to a
  transport.
- **NFR-D4** Likewise, repository methods return **domain entities**,
  never SQLAlchemy ORM rows. Mapping happens inside the repository
  adapter.

### 7.10 Repo hygiene & contributor workflow

- **NFR-R1** Dependency manager: **uv** (Astral). Lockfile `uv.lock` is
  committed. CI caches `~/.cache/uv` keyed on `uv.lock`.
- **NFR-R2** Config files at repo root:
  - `.gitignore` (Python, Docker, IDE)
  - `.editorconfig` (LF line endings, UTF-8, 4-space indent, trim
    trailing whitespace)
  - `.env.example` (every var from §8 with a safe placeholder)
  - `LICENSE` (placeholder until chosen)
  - `CONTRIBUTING.md` (how to run, test, lint, commit)
  - `.github/PULL_REQUEST_TEMPLATE.md`
  - `.pre-commit-config.yaml`
- **NFR-R3 Pre-commit hooks.** `.pre-commit-config.yaml` runs locally
  on every commit:
  - `ruff` (lint, autofix)
  - `ruff-format` (formatter)
  - `end-of-file-fixer`, `trailing-whitespace`,
    `check-merge-conflict`, `check-yaml`, `check-added-large-files`
  - `commitlint` (Conventional Commits — see NFR-R5)

  These mirror a strict subset of CI; failures surface in 2 seconds,
  not 4 minutes.
- **NFR-R4 Tool configuration.** `pyproject.toml` is the single home
  for `ruff`, `mypy`, `pytest`, and `coverage` config. No
  `setup.cfg` / `mypy.ini` / `pytest.ini` sprawl.
- **NFR-R5 Commit conventions.** **Conventional Commits**: `feat:`,
  `fix:`, `refactor:`, `test:`, `chore:`, `docs:`, `ci:`. Scope
  optional but encouraged (`feat(booking): …`). Body links the
  `FR-*` id when applicable. Enforced by `commitlint` in pre-commit
  and `commit-message` job in CI.
- **NFR-R6 PR template** at `.github/PULL_REQUEST_TEMPLATE.md`
  requires:
  - **Summary** — what & why (not how).
  - **Linked requirements** — FR ids covered.
  - **Test plan** — which tests prove it; what was tested manually.
  - **Risks / rollout notes** — anything reviewers should watch.
- **NFR-R7 Architecture Decision Records.** Light-weight ADRs live in
  `/adr/NNNN-title.md` (one page, template included). Three seeded
  ADRs at scaffold time:
  - `0001-clean-architecture-modular-monolith.md`
  - `0002-mock-payment-provider-first.md`
  - `0003-jwt-access-token-only.md`

  A fourth (`0004-event-delivery-in-process-sync.md`) records §7.8's
  choice and notes the outbox migration trigger.

---

## 8. Environment variables (initial set)

| Name                      | Required  | Purpose                                             |
| ------------------------- | --------- | --------------------------------------------------- |
| `APP_ENV`                 | yes       | `local` / `staging` / `prod`                        |
| `DATABASE_URL`            | yes       | Async SQLAlchemy DSN                                |
| `JWT_SECRET`              | yes       | HS256 signing key                                   |
| `JWT_EXPIRES_MINUTES`     | no        | Default 1440                                        |
| `CORS_ORIGINS`            | yes       | Comma-separated allowlist                           |
| `NOTIFICATION_PROVIDER`   | yes       | `console` \| `twilio`                               |
| `TWILIO_ACCOUNT_SID`      | if twilio | Twilio sandbox SID                                  |
| `TWILIO_AUTH_TOKEN`       | if twilio | Twilio sandbox token                                |
| `TWILIO_FROM_NUMBER`      | if twilio | Twilio sandbox sender                               |
| `PAYMENT_PROVIDER`        | yes       | `mock` (v1)                                         |
| `PAYMENT_WEBHOOK_SECRET`  | yes       | Used to sign/verify mock webhooks                   |
| `BOOKING_PAYMENT_TIMEOUT` | no        | Minutes before PENDING_PAYMENT expires (default 15) |

---

## 9. Open questions deferred to later

These don't block v1 but should be revisited before a real launch:

- Real cancellation policy (flexible/moderate/strict per property).
- Tenant refund on tenant-initiated cancellation.
- Email channel + in-app notifications.
- Image uploads + object storage adapter.
- Stripe adapter and migration of existing mock data.
- Audit log of all state transitions (separate from notifications).
- Per-IP and per-user rate limiting.
- Internationalization of SMS templates.

---

## 10. Definition of done for v1

A v1 build is considered done when, against a fresh checkout:

1. `docker compose up --build` boots API + Postgres.
2. `alembic upgrade head` produces the full schema.
3. Through the OpenAPI docs, a developer can:
   - sign up as a landlord, create a property,
   - sign up as a tenant, list properties filtered by city/dates,
   - create a booking, create an intent, fire the mock confirm, see the
     booking move to `PENDING_APPROVAL`, see the SMS logged (console sender)
     or delivered (Twilio sandbox),
   - log in as the landlord, accept the booking, see the tenant SMS,
   - alternately decline / cancel and see a refund record + tenant SMS.
4. `pytest` is green, including the end-to-end smoke test.
5. Linting (`ruff`) and type checks (`mypy` on `src/`) are green.
6. **GitHub Actions CI is green on the merge commit**: `lint`, `typecheck`,
   `test`, and `migrations-check` jobs all pass, and overall coverage is
   ≥ 80% with domain + application modules ≥ 90% each.
7. Branch protection on `main` is enabled and requires the four jobs above
   to pass before merge.

---

## 11. Development workflow — TDD

The codebase is grown **test-first**. Every functional requirement
(`FR-*`) starts as a failing test and is considered "done" only when its
test passes inside CI. This is non-negotiable for the domain and
application layers; pragmatism is allowed for thin glue code in
infrastructure/interfaces.

### 11.1 The loop

For each FR or vertical slice of one:

1. **Red.** Write a failing test in `tests/unit/<module>/` that expresses
   the behavior in domain language. Name it after the rule, not the
   function (`test_cannot_book_overlapping_confirmed_range`, not
   `test_bookings_service_create`). Run it; confirm it fails for the right
   reason.
2. **Green.** Write the **smallest** code in the domain/application layer
   that makes the test pass. No speculative parameters, no early
   abstraction.
3. **Refactor.** With the test still green, clean up names, extract value
   objects, deduplicate. The test is the safety net.
4. **Widen the net.** Add edge-case tests (boundary dates, off-by-one,
   currency mismatch, idempotency on repeated webhook). Only then move on.

### 11.2 Order of work per module

Implement each bounded context (auth → property → booking → payment →
notification) in this order so dependencies flow inward and tests stay
honest:

1. **Domain entities + value objects** with unit tests (`Money`,
   `DateRange.overlaps`, `Booking.transition_to`).
2. **Application use cases** against in-memory fakes of every port.
3. **Infrastructure adapters** (SQLAlchemy repos, Twilio client, mock
   payment provider) with integration tests against real Postgres / fake
   HTTP.
4. **HTTP interface** (FastAPI router) with e2e tests through
   `httpx.AsyncClient`.
5. Only now, wire the module into the app factory.

This sequence guarantees that by the time a route exists, the behavior it
exposes is already proven at the lower layer.

### 11.3 Rules of thumb

- **NFR-W1** Don't write production code without a failing test that needs
  it. If you're tempted, the test is missing.
- **NFR-W2** One assertion concept per test. Multiple `assert`s are fine
  when they describe the same outcome; if they describe different outcomes,
  split the test.
- **NFR-W3** Tests at the domain layer must read like product
  specifications. A reviewer who doesn't know Python should be able to
  understand intent from the test name + arrange/act/assert blocks.
- **NFR-W4** Bugs found in manual testing or production become regression
  tests **before** the fix is written. Same Red → Green → Refactor loop.
- **NFR-W5** A PR that lowers coverage on a touched module is rejected by
  CI, not by reviewers.
