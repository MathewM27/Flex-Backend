# api/

Outer HTTP layer. Owns the FastAPI app factory, middleware, exception
handlers, and the top-level router that mounts each module's router.

| File | Purpose |
| --- | --- |
| `app.py` | `create_app()` factory — assembles middleware, error handlers, routers |
| `routes.py` | Mounts `/api/v1`, declares `/health` and `/ready` |
| `middleware.py` | `RequestIdMiddleware` (NFR-X5) |
| `exception_handlers.py` | Maps `DomainError` → envelope (NFR-E2) |

Modules contribute routers to `routes.py` once they exist. This layer
**never** contains business rules.
