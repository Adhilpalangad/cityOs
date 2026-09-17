import asyncio
from collections.abc import Awaitable, Callable

import asyncpg
from aiokafka.admin import AIOKafkaAdminClient
from neo4j import AsyncGraphDatabase
from qdrant_client import AsyncQdrantClient
from redis.asyncio import Redis

from app.core.config import Settings

Check = Callable[[], Awaitable[None]]


async def _postgres(settings: Settings) -> None:
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


async def _neo4j(settings: Settings) -> None:
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    try:
        await driver.verify_connectivity()
    finally:
        await driver.close()


async def _qdrant(settings: Settings) -> None:
    client = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=2)
    try:
        await client.get_collections()
    finally:
        await client.close()


async def _kafka(settings: Settings) -> None:
    client = AIOKafkaAdminClient(bootstrap_servers=settings.kafka_brokers, request_timeout_ms=2000)
    await client.start()
    try:
        await client.list_topics()
    finally:
        await client.close()


async def dependency_status(settings: Settings) -> dict[str, str]:
    checks: dict[str, Check] = {
        "postgres": lambda: _postgres(settings),
        "redis": lambda: _redis(settings),
        "neo4j": lambda: _neo4j(settings),
        "qdrant": lambda: _qdrant(settings),
        "kafka": lambda: _kafka(settings),
    }

    async def run(name: str, check: Check) -> tuple[str, str]:
        try:
            await asyncio.wait_for(check(), timeout=3)
            return name, "healthy"
        except Exception:
            return name, "unhealthy"

    return dict(await asyncio.gather(*(run(name, check) for name, check in checks.items())))
