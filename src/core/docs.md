# core/

Process-level wiring that the rest of the codebase consumes but does not
depend on as a domain concern:

- `config.py` — pydantic-settings `Settings` loaded from env. Required values
  missing at startup abort the process (NFR-O2). `get_settings()` is cached;
  tests override via FastAPI `dependency_overrides`.
- `logging.py` — structlog setup with a `request_id` contextvar so every log
  line is automatically correlated (NFR-X5).
- `db.py` — async SQLAlchemy engine + per-request session factory. The
  `UnitOfWork` adapter in `shared/` wraps these for application use.

Nothing in `core/` knows about specific modules. Modules know about `core/`.
