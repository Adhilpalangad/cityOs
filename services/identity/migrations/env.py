import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.db import models  # noqa: F401 - registers tables on Base.metadata
from app.db.base import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", get_settings().async_database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        literal_binds=True,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(
            lambda conn: context.configure(connection=conn, target_metadata=target_metadata)
        )
        await connection.run_sync(lambda _: context.run_migrations())
        # PostgreSQL uses transactional DDL, and SQLAlchemy's asyncio
        # Connection autobegins a transaction on the first statement
        # `context.configure()` issues (checking `alembic_version`).
        # Alembic then sees a transaction it didn't start and doesn't
        # commit it, so without this the migration reports success but
        # silently rolls back when the connection closes -- SQLite (used
        # in this repo's unit tests) doesn't hit this because Alembic
        # treats it as non-transactional DDL and never defers the commit.
        await connection.commit()
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
