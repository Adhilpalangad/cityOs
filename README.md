# CityOS

CityOS is an Urban Intelligence & Operations Platform. This repository currently implements **Module 01** (repository, runtime, infrastructure, and developer platform), **Module 02** (identity, authentication, and RBAC), and **Module 03** (Roads, Hospitals, Vehicles, and Incidents). No AI, digital twin, simulation, or citizen-facing features are implemented yet, and only four of the city's domain entities exist so far.

## Prerequisites

- Node.js 20+ and npm 10+
- Python 3.12+
- Docker Engine with Docker Compose v2
- GNU Make (optional; every command can be run directly)

## Start locally

1. Copy `.env.example` to `.env`; development defaults work as-is and must not be used in production.
2. Run `make setup`.
3. Run `make infra-up`, then migrate each service: `make migrate service=identity`, `make migrate service=city-core`, `make migrate service=api-gateway`.
4. Start the identity service: `cd services/identity && uvicorn app.main:app --reload --port 8001`.
5. Start the city-core service: `cd services/city-core && uvicorn app.main:app --reload --port 8002`.
6. Start the API gateway: `cd services/api-gateway && uvicorn app.main:app --reload`.
7. In another terminal start the web app: `npm run dev:web`.
8. Open http://localhost:3000 and verify http://localhost:8000/ready.
9. Optionally, create the first administrator: set `SUPERADMIN_EMAIL`/`SUPERADMIN_PASSWORD` in `.env` and run `make bootstrap-admin`.

To build and run applications plus infrastructure in containers, use `docker compose --profile apps up --build`. Infrastructure alone is the default Compose profile.

## Repository structure

- `apps/web` — Next.js App Router application (status page plus the login/register/account flow)
- `services/api-gateway` — FastAPI entry point; proxies identity's and city-core's routes to their services, and owns readiness checks, tests, and its own Alembic migrations
- `services/identity` — Module 02: registration, login, JWT/refresh tokens, Google/GitHub OAuth, email verification, password reset, and RBAC (users, roles, departments, permissions); see [services/identity/README.md](services/identity/README.md)
- `services/city-core` — Module 03: Roads, Hospitals, Vehicles, and Incidents (full lifecycle), permission-gated against identity's tokens; see [services/city-core/README.md](services/city-core/README.md)
- `services/*` (other than `api-gateway`, `identity`, and `city-core`) — reserved boundaries for future services
- `packages/types`, `packages/validation` — TypeScript types and Zod schemas mirroring the identity service's Pydantic schemas, consumed by `apps/web`
- `packages/*` (the rest) — reserved boundaries for future modules
- `data-providers`, `ml` — reserved future integration and model boundaries
- `infrastructure` — local runtime support
- `tests` — cross-service test suites
- `docs` — architecture and development guidance

## Environment

All settings are documented in `.env.example`. Backend settings are typed and centralized in each service's `app/core/config.py`. Browser-visible variables must use the `NEXT_PUBLIC_` prefix. `.env` and derived secret files are ignored by Git. `JWT_SECRET` in particular must be replaced with a real random value outside local development (see the generation command in `.env.example`).

## Migrations

Each service owns its own Alembic history **and its own database** on the shared Postgres instance -- `cityos` (api-gateway), `cityos_identity`, `cityos_city_core` -- created by `infrastructure/postgres/init-databases.sql`, which only runs the first time a fresh `postgres_data` volume initializes. Sharing one database across services was tried and reverted: independent Alembic histories collided in a single `alembic_version` table the moment two services' revision IDs diverged. If you created the `postgres_data` volume before this existed, either recreate it (`docker compose down -v && docker compose up -d`, dropping all local dev data) or create the two extra databases by hand: `docker compose exec postgres psql -U cityos -d postgres -c "CREATE DATABASE cityos_identity; CREATE DATABASE cityos_city_core;"`.

Pass `service=` (defaults to `identity`) to target one: `make migrate service=api-gateway`, `make migration service=city-core message=my_change`, `make downgrade service=identity`. `api-gateway`'s migration `0001` enables PostGIS and creates the `platform_metadata` proof table; `identity`'s `0001` creates the RBAC/user schema and `0002` seeds its default departments, permissions, and roles; `city-core`'s `0001` creates the roads/hospitals/vehicles/incidents schema.

## Quality and tests

- `make test` — frontend component tests and fast backend tests (all three services)
- `make lint` — ESLint, TypeScript, and Ruff (all three services)
- `make build` — production web and container builds
- `RUN_INTEGRATION_TESTS=1 pytest tests/integration` (from any service directory) — readiness against running infrastructure

Normal unit tests do not require Docker; `identity` and `city-core` run against an in-memory SQLite database. `/health` reports process health on every service. `/ready` performs live dependency checks (`api-gateway`: PostgreSQL, Redis, Neo4j, Qdrant, Kafka; `identity`/`city-core`: PostgreSQL, Redis) and returns HTTP 503 when any are unavailable.

## Common commands

`make setup`, `make dev`, `make infra-up`, `make infra-down`, `make logs`, `make test`, `make lint`, `make format`, `make migrate`, `make build`, `make health`, and `make bootstrap-admin` correspond directly to repository tasks.

Don't have `make` (e.g. plain Windows without Chocolatey/Scoop/WSL)? `make check` (lint + test everything, no Docker required) has a direct equivalent: run `scripts\check.ps1` from PowerShell or `bash scripts/check.sh` from Git Bash.

## Troubleshooting

- Inspect container failures with `docker compose ps` and `docker compose logs <service>`.
- Ensure ports 3000, 5432, 6379, 6333, 7474, 7687, 8000, 8001, 8002, 9000, 9001, and 19092 are free.
- A 503 from `/ready` is intentional if a dependency is down; inspect its `dependencies` object.
- After changing database credentials, update both `.env` and the persisted volume or recreate the development volume intentionally.
- A 502/503 from a proxied `/api/v1/...` call through the gateway usually means the downstream service (`identity` or `city-core`) isn't running, or its `*_SERVICE_URL` setting is wrong.
- `identity` and `city-core` verify tokens with the same `JWT_SECRET`; if it differs between them, every proxied request to `city-core` will 401.
- `docker compose up -d` failing with `pull access denied for minio/mc` (or `minio/minio`) means your Docker cache predates the fix -- MinIO stopped publishing to Docker Hub and only publishes to `quay.io` now; `docker-compose.yml` already points at `quay.io/minio/...`, so just re-run `docker compose up -d`.
- `ConnectionRefusedError` / `connection to server ... failed` from any `alembic upgrade` almost always means Docker Desktop isn't running or `docker compose up -d` hasn't finished yet -- check `docker compose ps` shows `postgres` as `healthy` first.
- A migration that logs success but a subsequent `alembic current` shows nothing, or a service 500s with `relation "..." does not exist`: this was a real bug in the async Alembic template used here (see `docs/development.md`) and is fixed as of the commit that added this line; if you still see it, your `services/*/migrations/env.py` predates the fix.
- The web app rendering with no styling at all (unstyled HTML, not just plain-looking) usually means `npm install`'s postinstall scripts were blocked -- npm 11 blocks them by default. Run `npm approve-scripts --allow-scripts-pending` (approve each listed package) and `npm rebuild`, then rebuild the app. `apps/web` uses Tailwind v3 specifically to avoid a related, unfixable-in-config issue: see `docs/development.md`.

See [architecture](docs/architecture.md) and [development](docs/development.md) for more detail.

