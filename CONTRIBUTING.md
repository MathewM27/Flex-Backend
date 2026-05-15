# Contributing to Flex Backend

This document explains how to set up a local environment, the rules a change
must satisfy before it can land, and the workflow we follow. The non-negotiables
are in [requirements.md](requirements.md) — this file is the operational guide.

---

## 1. Local setup

You need:

- **Python 3.12** (`uv` manages this for you; install once via
  [astral.sh/uv](https://docs.astral.sh/uv/))
- **Docker Desktop** (for Postgres + the API container)
- **Git**, with line endings set to LF (`.editorconfig` handles this in-editor)

```bash
# 1. Install dependencies (production + dev)
uv sync --group dev

# 2. Activate the venv if your shell doesn't do it for you
#    (uv run <cmd> handles this transparently)

# 3. Install pre-commit hooks (NFR-R3)
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg

# 4. Copy the env template
cp .env.example .env
# Edit .env, replace JWT_SECRET and PAYMENT_WEBHOOK_SECRET with real values.

# 5. Bring up the stack
docker compose up --build

# 6. Apply migrations in another terminal
docker compose exec api alembic upgrade head

# 7. Visit the API
#    http://localhost:8000/api/v1/docs
```

---

## 2. The TDD loop (NFR-W1)

This codebase is built **test-first** for the domain and application layers.
See [requirements.md §11](requirements.md) for the full rules.

```bash
# Run a tight, fast subset while iterating
uv run pytest tests/unit -q --tb=short

# Watch mode (re-run on file change) via pytest-watcher if you have it:
uv run ptw -- -q tests/unit

# Full suite, the same command CI runs
uv run pytest --cov=src --cov-fail-under=80
```

Rules of the loop:

1. **Red.** Write a failing test that expresses the rule, not the function.
2. **Green.** Smallest code to pass.
3. **Refactor.** Clean up with the test as your safety net.
4. **Widen.** Add edge-case tests before moving on.

Bugs found later become regression tests **before** the fix (NFR-W4).

---

## 3. Local checks before pushing

The pre-commit hooks catch most things; this is what CI will run end-to-end:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest --cov=src --cov-fail-under=80
uv run alembic upgrade head      # against a running Postgres
uv run alembic check             # no model/migration drift
```

A PR will not merge unless all four CI jobs (`lint`, `typecheck`, `test`,
`migrations-check`) are green (NFR-CI3).

---

## 4. Commit messages — Conventional Commits (NFR-R5)

Format: `<type>(<scope>): <subject>`

Types: `feat`, `fix`, `refactor`, `test`, `chore`, `docs`, `ci`, `perf`,
`build`, `style`, `revert`.

```text
feat(booking): reject overlapping confirmed range (FR-B3)
fix(payment): make webhook idempotent on replayed event id (FR-PAY4)
test(auth): cover signup with duplicate email (FR-A1)
refactor(shared): extract DateRange into value object
docs: add ADR 0005 for outbox migration trigger
```

The `commitlint` pre-commit hook enforces this on `git commit`. The body of
the commit should reference the relevant `FR-*` ids.

---

## 5. Branches and pull requests

- Branch from `main`. Naming: `<type>/<short-slug>` —
  e.g. `feat/booking-create-use-case`.
- Open a draft PR early; convert to ready when CI is green.
- The PR template in `.github/PULL_REQUEST_TEMPLATE.md` is mandatory.
- Squash-merge is the default. Keep the squashed commit message in the
  Conventional Commits format.
- Linear history. **No force-pushes to `main`.**

---

## 6. Architecture rules of thumb

(Full spec: [requirements.md §7.1–§7.10](requirements.md).)

- Domain depends on **nothing**. No FastAPI / SQLAlchemy / Twilio imports
  inside `src/modules/*/domain`.
- Application depends only on domain ports.
- Cross-module communication goes through **application services** or
  **domain events**, never direct table joins.
- Pydantic schemas live in `interfaces/`. Domain entities never leak to HTTP.
- Repositories return domain entities, never ORM rows.
- Use cases accept plain data, not Pydantic models.
- Errors: raise `DomainError` subclasses; the HTTP layer maps them.
- IDs: `UUIDv7` via `src.shared.ids.new_id()`. Never DB-generated integer ids.
- Time: `Clock` port; never `datetime.now()` directly. UTC-aware only.
- Money: `Money` value object; `float` near money is a bug.

---

## 7. Adding a new module

1. Add `src/modules/<name>/` with the four subfolders (`domain`,
   `application`, `infrastructure`, `interfaces`) and a `docs.md`.
2. Write the failing domain test under `tests/unit/<name>/`. Build the
   module bottom-up (domain → application → infrastructure → interface).
3. Register the SQLAlchemy ORM module in `alembic/env.py` so autogenerate
   sees the new tables.
4. Mount the FastAPI router from `interfaces/router.py` in
   `src/api/routes.py`.
5. Add module-specific ADRs to `adr/` if any decision is non-obvious.
