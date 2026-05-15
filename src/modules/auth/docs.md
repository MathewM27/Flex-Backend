# auth/

Owns: user signup, login, password hashing, JWT issuance, and the
"current user" dependency consumed by other modules.

| Layer | Contents (when implemented) |
| --- | --- |
| `domain/` | `User` entity, `Email` / `Password` value objects, `UserRepository` port |
| `application/` | `SignupUser`, `LoginUser`, `GetCurrentUser` use cases |
| `infrastructure/` | SQLAlchemy `UserRepository`, bcrypt hasher, `JoseJwtIssuer` |
| `interfaces/` | FastAPI router (`/auth/signup`, `/auth/login`, `/auth/me`), request/response schemas, `to_response` mapper |

**Status:** scaffold only. Implementation TDD'd in a subsequent commit.

**Related requirements:** FR-A1 — FR-A6, NFR-S1 — NFR-S3.
