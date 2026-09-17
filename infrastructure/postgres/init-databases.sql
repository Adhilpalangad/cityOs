-- Runs once, only when the postgres container initializes an empty data
-- directory (the official image's docker-entrypoint-initdb.d convention).
--
-- Each service gets its own database on the shared Postgres instance --
-- not just its own tables -- so independent Alembic histories never
-- collide in a shared `alembic_version` table, and no two services can
-- ever fight over a table name. `cityos` (created by the image itself
-- from POSTGRES_DB) stays api-gateway's platform database; this script
-- adds one more per downstream service.
CREATE DATABASE cityos_identity;
CREATE DATABASE cityos_city_core;
