# CONTINUE.md — picking up on a fresh machine

This file is a hand-off log. After the foundation commit lands on GitHub, use
these steps on any machine (your PC, a CI runner, a teammate's laptop) to
re-create the dev environment exactly and pick up where we left off.

> When the project stabilizes, this file gets deleted — `CONTRIBUTING.md`
> covers ongoing setup. For now it's the source of truth for *resuming*.

---

## 1. Where we left off (as of this commit)

**Phase 1 — Foundation: complete.** What's in:

- `pyproject.toml` with uv-managed deps and tool config (ruff, mypy, pytest, coverage).
- `src/` skeleton:
  - `src/main.py`, `src/api/` (app factory, `RequestIdMiddleware`,
    exception handlers, `/health` + `/ready`).
  - `src/core/` (settings, structlog, async DB engine).
  - `src/shared/` (errors, time/Clock, ids/UUIDv7, money, pagination,
    EventBus, UnitOfWork — all the cross-cutting primitives).
  - `src/modules/{auth,property,booking,payment,notification}/` with
    `docs.md` + empty `domain/application/infrastructure/interfaces/`
    folders. **No business logic yet** — those land via TDD next.
- `tests/` skeleton + 25 passing tests covering the shared primitives and
  an `/health` e2e smoke test.
- `alembic.ini` + `alembic/env.py` + `versions/` (no migrations yet — none
  needed until we land the first ORM model in the auth module).
- `Dockerfile` (multi-stage, non-root, healthcheck) + `docker-compose.yml`
  (api + Postgres 16) + `.dockerignore`.
- `.github/workflows/ci.yml` — five jobs: `lint`, `typecheck`, `test`,
  `migrations-check`, `docker-build`.
- `.pre-commit-config.yaml` — ruff, ruff-format, hygiene hooks,
  Conventional Commits.
- `CONTRIBUTING.md` + `.github/PULL_REQUEST_TEMPLATE.md`.
- `adr/` with 4 seeded ADRs.

**Local verification done on the laptop:**

- `uv sync --group dev` — clean
- `uv run ruff check .` — clean
- `uv run ruff format --check .` — clean
- `uv run mypy src` — clean (45 files)
- `uv run pytest tests/unit tests/e2e -q` — 25 passed in 7s
- `docker compose build api` — image built successfully
- `docker compose up` — **not yet run on the PC** (intentional; do step 7
  below)

**Next phase — Auth module (TDD):** see "What's next" at the bottom.

---

## 2. Prerequisites (install on the PC)

| Tool | Why | Version |
| --- | --- | --- |
| [Git](https://git-scm.com/downloads) | Pull the repo | latest |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Python dep manager | ≥ 0.10.11 |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Postgres + API container | latest |
| Optional: VS Code / Cursor | IDE | n/a |

Install uv on Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify:

```powershell
uv --version
python --version    # uv will install Python 3.12 if missing
docker --version
```

---

## 3. Clone the repo

```powershell
# Wherever you keep code
cd $HOME\OneDrive\Desktop
git clone https://github.com/<your-user>/Flex-Backend.git
cd Flex-Backend
```

> If you haven't pushed yet on the laptop, do that first. See "If you haven't
> pushed yet" at the bottom of this file.

---

## 4. Configure `.env`

```powershell
# Copy the template — never edit .env.example for real values.
Copy-Item .env.example .env

# Generate a real JWT secret (>= 32 chars).
$env:JWT_SECRET = python -c "import secrets; print(secrets.token_urlsafe(48))"
Write-Host $env:JWT_SECRET
# Paste that value into .env replacing the JWT_SECRET= placeholder.

# Replace PAYMENT_WEBHOOK_SECRET with any 32-char string for local dev.
```

The required keys (already listed in `.env.example`):

- `JWT_SECRET` — generate as above.
- `PAYMENT_WEBHOOK_SECRET` — any 16+ char string for local.
- The rest can stay at their defaults for local development.

> `.env` is `.gitignore`d. Never commit it.

---

## 5. Install Python deps

```powershell
uv sync --group dev
```

This reads `uv.lock` (committed) so you get *exactly* the same dependency
versions used on the laptop.

---

## 6. Install pre-commit hooks (NFR-R3)

```powershell
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

This wires `ruff`, `ruff-format`, EOF/whitespace/merge-conflict hygiene, and
Conventional Commits enforcement into every `git commit`.

---

## 7. Verify the stack boots end-to-end

```powershell
# 7a. Build + start postgres + api in the background
docker compose up -d --build

# 7b. Wait for both to be healthy (5–15s)
docker compose ps

# 7c. Hit /health — should return {"status":"ok"}
curl http://localhost:8000/api/v1/health

# 7d. Hit /ready — should return {"status":"ready"} (DB ping)
curl http://localhost:8000/api/v1/ready

# 7e. Open the auto-generated OpenAPI docs
Start-Process http://localhost:8000/api/v1/docs

# 7f. Tail logs if anything fails
docker compose logs -f api
```

When you're done:

```powershell
docker compose down            # stop, keep DB volume
docker compose down -v         # stop AND drop DB volume (fresh start next time)
```

---

## 8. Verify everything that CI verifies (locally)

These four commands are exactly what CI runs. They MUST all be green before
opening a PR.

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest --cov=src --cov-report=term-missing:skip-covered --cov-fail-under=80
```

Migration check (needs Postgres running — `docker compose up -d postgres`):

```powershell
# Point alembic at the host port the compose Postgres exposes
$env:DATABASE_URL = "postgresql+asyncpg://flex:flex@localhost:5432/flex"
uv run alembic upgrade head
uv run alembic check
```

---

## 9. Daily dev loop (TDD)

```powershell
# Fast unit tests while iterating on the domain
uv run pytest tests/unit -q --tb=short

# Full suite before pushing
uv run pytest --cov=src --cov-fail-under=80

# Hot-reload server (alternative to docker compose up)
uv run uvicorn src.main:app --reload
```

---

## 10. What's next — Phase 2: Auth module (TDD)

When you're back, the next vertical slice is the **auth module** built
test-first per [requirements.md §11.2](requirements.md):

1. **Domain** (`src/modules/auth/domain/`):
   - `Email` value object (validation, normalization)
   - `Password` value object (hashing port boundary)
   - `User` entity (id, email, password_hash, full_name, role, phone)
   - `Role` enum (`TENANT`, `LANDLORD`)
   - `UserRepository` port
   - Unit tests first under `tests/unit/auth/`.
2. **Application** (`src/modules/auth/application/`):
   - `SignupUser`, `LoginUser`, `GetCurrentUser` use cases
   - `PasswordHasher` port, `JwtIssuer` port
   - Unit tests with in-memory fakes.
3. **Infrastructure** (`src/modules/auth/infrastructure/`):
   - SQLAlchemy `users` table + `SqlAlchemyUserRepository`
   - `BcryptPasswordHasher`, `JoseJwtIssuer`
   - First Alembic migration: `0001_create_users_table`
   - Integration tests against real Postgres.
4. **Interfaces** (`src/modules/auth/interfaces/`):
   - Pydantic schemas, mapper, FastAPI router for
     `POST /auth/signup`, `POST /auth/login`, `GET /auth/me`.
   - E2E tests through the ASGI client.
5. Wire the router into `src/api/routes.py`. Register
   `src.modules.auth.infrastructure.orm` in `alembic/env.py`.

Covers FR-A1 through FR-A6.

---

## If you haven't pushed yet (still on the laptop)

```bash
# 1. Stage everything new from this phase
git add .

# 2. Conventional Commits format. Use --no-verify only if pre-commit
#    isn't installed yet (it gets installed in step 6 above).
git commit -m "feat: scaffold foundation (deps, src, tests, ci, adrs)" --no-verify

# 3. Add the remote (skip if already added) and push
git remote -v        # check what's there
git push origin main

# Now on the PC, follow steps 2–8.
```
