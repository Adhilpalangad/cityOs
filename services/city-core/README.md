# City Core Service

The Module 03 FastAPI service that owns the city's core operational
entities: Roads, Hospitals, Vehicles, and Incidents. From this directory,
install with `pip install -e ".[dev]"`, run with
`uvicorn app.main:app --reload --port 8002`, and test with `pytest`.

## What this service owns

- Roads: capacity, traffic level, risk level, and a simple waypoint list
- Hospitals: bed/ICU capacity and emergency load
- Vehicles: registration and live position (matches the Vehicle Data
  Provider event shape from spec section 14)
- Incidents: the full lifecycle from spec section 16 --
  `DETECTED -> VERIFIED -> ASSIGNED -> RESPONDING -> RESOLVED -> ANALYZED`,
  enforced by `app/services/incidents.py` so the API can never skip a stage
  or move backwards. Incidents are never hard-deleted (spec section 10:
  "Create, Read, Update, Resolve/archive").

It does not own Departments (that's `identity`'s RBAC) or Buildings (a
better fit for the future Infrastructure Management module).

## Geography: a placeholder, not PostGIS -- yet

Roads store waypoints as a plain `[[lat, lon], ...]` JSON list, and
Hospitals/Vehicles/Incidents store a plain `latitude`/`longitude` pair,
rather than real PostGIS `LINESTRING`/`POINT` geometry columns. This is
intentional for this module: it keeps the schema identical across
PostgreSQL and the SQLite database the unit test suite runs against (no
SpatiaLite extension required), which matters more right now than spatial
queries no other module needs yet. When the Digital Twin or Traffic
Intelligence module actually needs `ST_DWithin`/nearest-neighbor queries
(spec section 34's worked examples), that's the point to introduce
GeoAlchemy2 and a real PostGIS column -- likely via a dedicated migration
that backfills geometry from these lat/lon values, not a rewrite.

## Authorization

city-core never issues tokens -- only `identity` does. It verifies the
same HS256 JWT using the shared `JWT_SECRET` and trusts the permission
list baked into the token at issuance (see identity's README for that
trade-off). `app/core/security.py` explains why this is a small
intentional duplicate of identity's decode-side code rather than a shared
package.

## Live data pipeline

`data-providers/traffic` and `data-providers/vehicles` are standalone
synthetic data services (spec section 28) -- not sensors, software
services that emulate the interface a real traffic/GPS system would
publish. Each publishes to Redpanda (`traffic.events` / `vehicle.events`)
on every tick. `app/services/live_ingest.py` upserts the matching Road
(by `code`) or Vehicle (by `vehicle_id`) row from each event -- creating
it on first sight, since these tables have no separate seed data -- and
`app/api/routes_live.py` runs the Kafka consumer as a background task
(started from `app/main.py`'s lifespan, skipped under `APP_ENV=test`)
and rebroadcasts each update over `/ws/live`. `services/api-gateway`
relays that endpoint to the browser (`app/api/ws_proxy.py`). Browsers
can't set a WebSocket handshake's `Authorization` header, so the access
token travels as a `?token=` query parameter instead.
`hospitals`/`weather`/`energy`/`water`/`incidents` providers aren't wired
in yet -- `hospitals` exists but is missing its `pyproject.toml`; the
rest are empty.

## Tests

Unit tests run against an in-memory SQLite database (no Docker required)
via `tests/conftest.py`. Since this service has no users of its own,
tests mint access tokens directly with `tests/helpers.py`'s `make_token`,
signed with the same test `JWT_SECRET` the app reads -- there is no need
to run identity's full register/login flow to test permission
enforcement here. `tests/integration/test_readiness.py` checks `/ready`
against real Postgres/Redis and is skipped unless `RUN_INTEGRATION_TESTS=1`.
