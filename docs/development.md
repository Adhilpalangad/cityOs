# Development conventions

Copy `.env.example` to `.env` and keep credentials local. Add backend configuration only to the typed `Settings` class and the example environment file. Frontend public configuration belongs in `src/lib/env.ts`; never expose secrets via `NEXT_PUBLIC_` variables.

Keep API routes thin, typed, and versioned when they are public platform APIs. Use the centralized error foundation, preserve `X-Request-ID`, and emit structured logs. Readiness probes must perform real bounded-time connectivity checks; liveness probes must remain independent of infrastructure.

Alembic owns schema changes. Every schema change requires an upgrade and safe downgrade. Unit tests stay independent of Docker; mark infrastructure tests as integration tests and run them explicitly.

Before submitting changes, run `make lint`, `make test`, `npm run build:web`, and `docker compose config`. Do not add future domain behavior to foundation packages.

For any `updated_at` (or similar) column, use `onupdate=<a Python callable>` (see `_utcnow()` in identity's and city-core's `app/db/models.py`), never `onupdate=sa.func.now()`. A server-side `onupdate` needs its post-UPDATE value fetched back from the database before it can be read; on SQLite via `aiosqlite` that fetch does not happen automatically, so reading the attribute on the same ORM object right after `await db.commit()` (without an intervening reload) raises `MissingGreenlet`. A Python-side callable sets the value locally at flush time instead, with no round trip and no portability gap between SQLite (tests) and PostgreSQL.

Every service's `migrations/env.py` must call `await connection.commit()` after `context.run_migrations()` inside `run_async_migrations()` (it does; keep it if you regenerate this file). Without it, `alembic upgrade head` against PostgreSQL logs every migration as applied and exits 0, but nothing persists: `context.configure()` issues a query that autobegins a transaction on the async connection before Alembic's own `begin_transaction()` runs, so Alembic sees a transaction it didn't start and assumes the caller owns committing it -- which the official async template's `async with connectable.connect() as connection:` block never does, so the transaction silently rolls back when the connection closes. This only shows up against PostgreSQL ("transactional DDL"); it never reproduces against SQLite ("non-transactional DDL", used by every service's unit tests), which is exactly why it shipped unnoticed and only surfaced testing against real Postgres.

Each service also gets its **own Postgres database**, not just its own tables (`cityos`, `cityos_identity`, `cityos_city_core` -- see `infrastructure/postgres/init-databases.sql` and `docs/architecture.md`). A new service's default `database_url` in `app/core/config.py` must point at a new database name, and `docker-compose.yml`'s `DATABASE_URL` for that service's container must match; do not default a new service to an existing database's name, even temporarily -- two services' Alembic histories sharing one `alembic_version` table fail the moment their revision IDs diverge, which will not be obvious from either service's own migration output.

## Frontend styling: Tailwind v3, deliberately not v4

`apps/web` pins `tailwindcss@3` with a standard PostCSS + `tailwind.config.ts`
setup, not v4's CSS-first `@theme`/`@import "tailwindcss"` config, even
though v4 was current when this app was built. This was a deliberate
downgrade, not an oversight: v4's PostCSS plugin depends on a native Rust
binary (`@tailwindcss/oxide`) to scan the filesystem for class names, and on
at least one real development machine that binary's file I/O silently
returned nothing -- `scanFiles({content})` correctly extracted candidates
from a string, but `scanFiles({file})` and directory-based `scan()` both
returned zero results for files that definitely existed, with no error. That
is the signature of security software (Windows Defender or similar)
transparently blocking an unsigned native addon's low-level file access --
not something a project can fix in its own config, and not something you
can assume is off on every contributor's machine. Tailwind v3's content
scanning goes through plain Node `fs` instead, which is unaffected. Moving
back to v4 risks "the build succeeds but zero CSS is generated" reappearing
silently on some fraction of Windows machines with real-time antivirus
enabled -- which is most of them; don't, unless that risk has been
addressed some other way.

The design-token approach survives the downgrade unchanged: colors are CSS
custom properties on `:root` in `globals.css` that flip with
`prefers-color-scheme`, and `tailwind.config.ts`'s `theme.extend.colors`
just aliases each one (`brand: "var(--brand)"`, ...), so utilities like
`bg-brand`/`text-ink-muted` resolve automatically per theme with no `dark:`
variant needed anywhere.

## Identity and RBAC (Module 02)

`identity` follows the same conventions as `api-gateway` (structlog request
logging, the `{"error": {...}}` envelope, `/health` vs `/ready`, Alembic with
upgrade/downgrade pairs) plus a few of its own:

- RBAC defaults (departments, permissions, roles) live in exactly one place,
  `app/db/seed_data.py`; both migration `0002` and the test fixtures import
  it, so it never drifts from what actually gets seeded. Changing a default
  means editing that file and adding a new migration, not editing `0002`.
- Authorization is a JWT decode, not a database query: access tokens carry
  the caller's resolved permission list at issuance time. See
  `services/identity/README.md` for the trade-off this implies.
- The gateway proxies identity's routes rather than reimplementing or
  calling into them directly (`app/api/proxy.py`); a new domain service
  should be proxied the same way, not merged into the gateway process.
- `packages/types` and `packages/validation` mirror the identity service's
  Pydantic schemas by hand (TypeScript interfaces / Zod schemas). Renaming
  or changing a field on one side means updating the other in the same
  change.

## City core (Module 03)

`city-core` follows the same conventions again, plus:

- It has no users and issues no tokens. It verifies the JWTs `identity`
  issued using the same shared `JWT_SECRET` (`app/core/security.py` /
  `app/api/deps.py` are a small intentional duplicate of identity's
  decode-side code -- see that module's docstring for why this isn't a
  shared package). Keeping `JWT_SECRET` identical across services is a
  deployment requirement, not just a default.
- Cross-service references (an incident's `department_code`) are plain
  codes, not foreign keys -- there is no database city-core could
  foreign-key into for a table that lives in `identity`.
- Geometry is a placeholder (plain lat/lon columns, a JSON waypoint list),
  not PostGIS, so the schema is identical on SQLite and PostgreSQL. See
  `services/city-core/README.md` for when to introduce GeoAlchemy2.
- A workflow with an explicit lifecycle (incidents: `DETECTED -> ... ->
  ANALYZED`) gets its transition rules enforced in one place
  (`app/services/incidents.py`), not scattered across route handlers.

