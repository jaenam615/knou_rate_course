"""
Redis client for caching and trending searches.

When REDIS_URL is not configured, returns None and the app falls back to in-memory cache.
"""

import logging

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None
_redis_initialized: bool = False


def is_redis_configured() -> bool:
    """Check if Redis is configured."""
    return bool(settings.redis_url)


async def get_redis() -> redis.Redis | None:
    """Get or create Redis client. Returns None if Redis is not configured."""
    global _redis_client, _redis_initialized

    if not is_redis_configured():
        return None

    if not _redis_initialized:
        try:
            _redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await _redis_client.ping()
            _redis_initialized = True
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning("Redis connection failed, using in-memory cache: %s", e)
            _redis_client = None
            _redis_initialized = True

    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client, _redis_initialized
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
    _redis_initialized = False
