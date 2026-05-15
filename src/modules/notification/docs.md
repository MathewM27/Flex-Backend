# notification/

Owns: outbound SMS via the `NotificationSender` port. Subscribes to domain
events from the booking module and dispatches messages.

| Layer | Contents (when implemented) |
| --- | --- |
| `domain/` | `Notification` entity, `NotificationSender` port, template registry |
| `application/` | Event handlers (`on_booking_paid`, `on_booking_accepted`, etc.) |
| `infrastructure/` | `TwilioSmsSender` adapter, `ConsoleSmsSender` adapter (dev), SQLAlchemy repo for sent notifications |
| `interfaces/` | (none in v1 — notifications are not directly callable via HTTP) |

**Status:** scaffold only.

**Related requirements:** FR-N1 — FR-N4.
