# syntax=docker/dockerfile:1.7
# Multi-stage build:
#   1. `builder` resolves deps with uv and installs them into a venv.
#   2. `runtime` is a slim image with only the venv + source.
# Final image runs as a non-root user.

ARG PYTHON_VERSION=3.12-slim-bookworm

# ──────────────────────────────────────────────────────────────────────────────
# Stage 1 — build (resolve + install deps with uv)
# ──────────────────────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION} AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Install uv (pinned)
COPY --from=ghcr.io/astral-sh/uv:0.10.11 /uv /uvx /usr/local/bin/

WORKDIR /app

# Install deps first so they cache when only source changes.
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev || \
    uv sync --no-install-project --no-dev

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2 — runtime
# ──────────────────────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app

# Create a non-root user
RUN groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app

# Copy the resolved venv from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy source after deps so source changes don't bust the dep layer
COPY --chown=app:app src ./src
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app alembic.ini ./

USER app

EXPOSE 8000

# Healthcheck hits the API's /health endpoint
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; \
        sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/v1/health', timeout=2).status == 200 else 1)"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
