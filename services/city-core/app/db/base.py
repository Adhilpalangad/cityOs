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
        # Unit tests use an in-memory SQLite database; a single pooled
        # connection keeps the schema and data alive for the engine's life.
        from sqlalchemy.pool import StaticPool

        kwargs = {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
    return create_async_engine(url, **kwargs)


engine = build_engine()
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
