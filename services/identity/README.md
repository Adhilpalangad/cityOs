# Identity Service

The Module 02 FastAPI service that owns authentication, tokens, and RBAC:
users, roles, permissions, and departments. From this directory, install
with `pip install -e ".[dev]"`, run with `uvicorn app.main:app --reload --port 8001`,
and test with `pytest`.

## What this service owns

- Registration, login, logout, email verification, and password reset
- JWT access tokens (15 min) and rotating opaque refresh tokens (7 days)
- Google and GitHub OAuth 2.0 (authorization-code flow)
- Users, Roles, Departments, and Permissions CRUD, all permission-gated
- The canonical RBAC seed data (`app/db/seed_data.py`), applied by
  migration `0002`

It does not own session storage for the browser, UI, or any domain data
(roads, incidents, hospitals, ...) -- those belong to later modules. The
`api-gateway` proxies `/api/v1/auth`, `/api/v1/users`, `/api/v1/roles`,
`/api/v1/departments`, and `/api/v1/permissions` to this service, so the
frontend and other clients only ever need to know the gateway's URL.

## Password storage and tokens

Passwords are hashed with Argon2id (`argon2-cffi`), never stored in
plaintext. Access tokens are HS256 JWTs signed with `JWT_SECRET` and carry
the caller's role, department, and *resolved* permission list, so
authorization on every other request is a single decode with no database
round trip -- the trade-off is that a role or permission change takes
effect on the user's next login or token refresh, not immediately.
Refresh, email-verification, and password-reset tokens are random opaque
strings; only their SHA-256 hash is ever persisted, so a database leak
does not hand out usable tokens. Refresh tokens rotate on every use and
the previous token is marked revoked and linked via `replaced_by_id`, so a
stolen, already-used refresh token cannot be replayed.

## Email

There is no SMTP/SES integration -- CityOS is software-only, and wiring a
real mail transport in is a deployment concern. `app/services/email.py`
logs every dispatch via structlog and, outside `APP_ENV=production`, also
appends to an in-process outbox so tests and local development can see
exactly what a verification or password-reset email would have said.

## Bootstrapping the first administrator

Creating a user through the API requires an existing user with
`user.create`, so the very first `SUPER_ADMIN` account has to be created
out of band:

```bash
SUPERADMIN_EMAIL=admin@cityos.example SUPERADMIN_PASSWORD=change-me-now \
    python -m scripts.bootstrap_admin
```

It is idempotent and safe to re-run; it only ever inserts a row when that
email does not already exist. `make bootstrap-admin` runs this using the
`SUPERADMIN_EMAIL`/`SUPERADMIN_PASSWORD` values from `.env`.

## Tests

Unit tests run against an in-memory SQLite database (no Docker required)
via `tests/conftest.py`, which builds the schema directly from the SQLAlchemy
models rather than running Alembic. `tests/integration/test_readiness.py`
checks `/ready` against real Postgres/Redis and is skipped unless
`RUN_INTEGRATION_TESTS=1`, matching `api-gateway`'s convention.
