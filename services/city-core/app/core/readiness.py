import asyncio
from collections.abc import Awaitable, Callable

import asyncpg
from redis.asyncio import Redis

from app.core.config import Settings

Check = Callable[[], Awaitable[None]]


async def _postgres(settings: Settings) -> None:
    if settings.async_database_url.startswith("sqlite"):
        return
    url = settings.async_database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    connection = await asyncpg.connect(url, timeout=2)
    try:
        await connection.fetchval("SELECT 1")
    finally:
        await connection.close()


async def _redis(settings: Settings) -> None:
    client = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
    try:
        if not await client.ping():
            raise ConnectionError("Redis ping failed")
    finally:
        await client.aclose()


async def dependency_status(settings: Settings) -> dict[str, str]:
    checks: dict[str, Check] = {
        "postgres": lambda: _postgres(settings),
        "redis": lambda: _redis(settings),
    }

    async def run(name: str, check: Check) -> tuple[str, str]:
        try:
            await asyncio.wait_for(check(), timeout=3)
            return name, "healthy"
        except Exception:
            return name, "unhealthy"

    return dict(await asyncio.gather(*(run(name, check) for name, check in checks.items())))
