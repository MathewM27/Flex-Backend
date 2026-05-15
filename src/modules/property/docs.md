# property/

Owns: landlord property CRUD and the tenant-facing list/filter endpoints.

| Layer | Contents (when implemented) |
| --- | --- |
| `domain/` | `Property` entity, `PropertyRepository` port, `PropertyFilter` value object |
| `application/` | `CreateProperty`, `UpdateProperty`, `DeleteProperty`, `ListProperties`, `GetProperty` |
| `infrastructure/` | SQLAlchemy `PropertyRepository` with city-ILIKE + date-overlap queries |
| `interfaces/` | FastAPI router (`/properties/*`), request/response schemas, mapper |

**Status:** scaffold only.

**Related requirements:** FR-P1 — FR-P6.
