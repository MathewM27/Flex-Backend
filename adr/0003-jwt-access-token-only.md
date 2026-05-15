# 0003 — JWT access token only (no refresh tokens)

- **Status:** Accepted
- **Date:** 2026-05-15
- **Deciders:** Mathews Mwangi

## Context

The frontend is a separate Next.js app served from a different origin. It
needs a way to authenticate against this API. Common options are
session cookies, JWT access + refresh tokens, or a single JWT.

Constraints:

- "Just simple auth — sign up with email/password and role." (requirements §4.1)
- One Next.js codebase consuming a separate API on a different host.
- Minimal but real security (NFR-S1–S3).
- No requirement for MFA, OAuth, or social login in v1.

## Decision

Use a **single JWT access token** signed with HS256. No refresh token.

- TTL configurable; default 24 hours (long enough that re-login friction
  is rare; short enough that revocation latency is bounded).
- Signed with `JWT_SECRET`, required at startup; the app refuses to
  boot without it (NFR-S2).
- Stored by the frontend in an `httpOnly` cookie via a Next.js route
  handler, never in `localStorage`
  ([frontendRequirements.md §9](../frontendRequirements.md)).
- Carries `sub` (user id), `role`, and `exp`. No other claims in v1.
- Role-based authorization is the FastAPI dependency that decodes the
  token and asserts the role.

## Consequences

**Positive**

- Trivial to implement and to reason about.
- No refresh-token rotation complexity, no token storage in DB.
- Compatible with a httpOnly-cookie frontend strategy, sidestepping
  XSS-stealable storage.

**Negative / trade-offs**

- Revocation before TTL expiry is impossible (this is a known JWT
  limitation). Acceptable while no high-privilege actions exist.
- 24h TTL means a compromised token is usable for up to a day. We'll
  cut the TTL or move to refresh tokens before adding sensitive
  operations (payouts, account deletion).
- No "log me out everywhere" until we add a refresh-token + revocation
  list.

## Alternatives considered

- **Session cookies.** Better security defaults but more friction with
  a separate-origin Next.js frontend (CSRF, SameSite=Strict caveats).
- **Access + refresh tokens.** Pays a complexity tax we don't yet need.
  Easy migration target later — add a `/auth/refresh` endpoint and a
  short access TTL; the rest of the system doesn't change.
