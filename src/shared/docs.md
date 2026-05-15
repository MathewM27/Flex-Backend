# shared/

Cross-cutting building blocks that all modules depend on. **No module-specific
domain logic** lives here.

| File | Purpose | Requirement |
| --- | --- | --- |
| `errors.py` | `DomainError` hierarchy + every error code | NFR-E1, NFR-E5 |
| `time.py` | `Clock` port + `SystemClock` / `FixedClock` + naive-datetime guard | NFR-X2, NFR-T6 |
| `ids.py` | `UUIDFactory` port + `new_id()` (UUIDv7) + `DeterministicUUIDFactory` | NFR-X1, NFR-T6 |
| `money.py` | `Money` value object — `Decimal` + currency, never `float` | NFR-X3 |
| `pagination.py` | `Page[T]` envelope used by every list endpoint | NFR-X4 |
| `events.py` | `EventBus` port + `InProcessEventBus` adapter | NFR-EV1, NFR-EV2 |
| `unit_of_work.py` | `UnitOfWork` port + `SqlAlchemyUnitOfWork` adapter | NFR-TX1, NFR-EV1 |

Adding a new shared primitive? It belongs here only if **at least two
modules** would consume it. Otherwise it lives inside the module that owns it.
