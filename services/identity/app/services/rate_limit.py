"""Fixed-window rate limiting backed by Redis.

Used to enforce the login policy from spec section 54 (5 attempts/minute).
If Redis is unreachable the limiter fails open -- it allows the request and
logs a warning -- so an unrelated cache outage never locks every user out
of authentication.
"""

import structlog
from redis.asyncio import Redis

from app.core.config import Settings

logger = structlog.get_logger()


async def check_rate_limit(
    settings: Settings, *, key: str, limit: int, window_seconds: int
) -> bool:
    """Return True if the request is allowed under the limit."""
    redis_key = f"ratelimit:{key}"
    try:
        client = Redis.from_url(settings.redis_url, socket_connect_timeout=1)
        try:
            count = await client.incr(redis_key)
            if count == 1:
                await client.expire(redis_key, window_seconds)
            return count <= limit
        finally:
            await client.aclose()
    except Exception:
        logger.warning("rate_limit_check_failed_open", key=key)
        return True
