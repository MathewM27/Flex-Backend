# payment/

Owns: payment intents, webhook handling, refunds. The whole module is built
behind a `PaymentProvider` port so swapping the mock for Stripe is a new
adapter, not a domain change.

| Layer | Contents (when implemented) |
| --- | --- |
| `domain/` | `Payment` + `Refund` entities, `PaymentProvider` port, `WebhookEvent` value object |
| `application/` | `CreateIntent`, `HandleWebhook` (idempotent), `IssueRefund` |
| `infrastructure/` | `MockPaymentProvider` (signs/verifies its own webhooks), SQLAlchemy repos |
| `interfaces/` | FastAPI router (`/payments/intent`, `/payments/mock/confirm`, `/payments/webhook`, `/payments/booking/{id}`) |

**Status:** scaffold only.

**Related requirements:** FR-PAY1 — FR-PAY6.
