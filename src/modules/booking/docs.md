# booking/

Owns: the booking lifecycle and the availability calendar.

State machine (full version in [requirements.md §4.3](../../../requirements.md)):

    PENDING_PAYMENT → PENDING_APPROVAL → CONFIRMED | DECLINED | CANCELLED | EXPIRED

| Layer | Contents (when implemented) |
| --- | --- |
| `domain/` | `Booking` aggregate (transitions + invariants), `DateRange` value object, `BookingRepository` port, domain events |
| `application/` | `CreateBooking`, `AcceptBooking`, `DeclineBooking`, `CancelBooking`, `ListBookings`, `ExpirePendingPayments` |
| `infrastructure/` | SQLAlchemy repo with `SELECT … FOR UPDATE` on property row for overlap (NFR-TX2) |
| `interfaces/` | FastAPI router (`/bookings/*`), schemas, mapper |

**Status:** scaffold only.

**Related requirements:** FR-B1 — FR-B9, NFR-TX2.
