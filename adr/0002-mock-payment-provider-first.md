# 0002 — Mock payment provider first

- **Status:** Accepted
- **Date:** 2026-05-15
- **Deciders:** Mathews Mwangi

## Context

The v1 build needs an end-to-end booking-and-pay flow visible from the
frontend, but we have no contract with Stripe or PayPal yet. The flow
must be production-shaped — webhook-driven, idempotent, refundable — so
that swapping in a real provider later is purely an adapter change.

## Decision

Ship a `MockPaymentProvider` adapter behind a `PaymentProvider` port. The
mock:

- Issues `PaymentIntent`s with a `client_secret` field whose name and
  shape mirror Stripe so the frontend integration is identical.
- On `POST /payments/mock/confirm`, the mock backend signs and posts a
  webhook to its own `/payments/webhook` endpoint. The booking only
  transitions on the **webhook**, not on the confirm call (FR-PAY2),
  which forces the async-confirmation code path Stripe will use.
- Verifies the webhook signature with a shared HMAC secret
  (`PAYMENT_WEBHOOK_SECRET`).
- Implements idempotency keyed on the provider event id (FR-PAY4).

## Consequences

**Positive**

- We can demo the entire booking → pay → approval flow without legal,
  KYC, or test-mode credentials.
- Migration to Stripe is a single new adapter file plus an env switch.
- The async-confirmation race we'll hit in production is exercised by
  tests today (NFR-T7).

**Negative**

- "Mock that pretends to be Stripe" is a small surface to maintain. We
  delete it the day a real provider lands and replace it with the
  Stripe adapter.
- No real card/3DS flow is exercised; the frontend's card form is
  visual-only.

## Alternatives considered

- **Skip payment entirely in v1.** Would force a major refactor when
  payment landed (it touches booking state transitions and refunds).
- **Stripe test mode now.** Adds account setup, key rotation, webhook
  tunneling, and a real external dependency to local dev. Premature.
