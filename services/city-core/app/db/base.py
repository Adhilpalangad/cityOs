from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def build_engine():
    settings = get_settings()
    url = settings.async_database_url
    kwargs: dict = {}
    if url.startswith("sqlite"):
        kwargs = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in url:
            # In-memory SQLite (unit tests) needs a single pooled connection
            # -- every new connection to `:memory:` otherwise gets its own
            # empty database, wiping the schema/data between queries.
            # StaticPool is *only* correct for :memory:; applying it to a
            # file-based SQLite database (e.g. someone running this service
            # locally without Docker) hangs every query past the first --
            # StaticPool forces every session onto the one shared
            # connection, and that serialization deadlocks against
            # aiosqlite's own per-connection background thread. A file-based
            # database doesn't need connection persistence like :memory:
            # does, so it just uses SQLAlchemy's normal pool.
            from sqlalchemy.pool import StaticPool

            kwargs["poolclass"] = StaticPool
    return create_async_engine(url, **kwargs)


engine = build_engine()
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
