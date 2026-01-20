"""
Cache dependency that provides the appropriate backend.

Uses Redis when configured, falls back to in-memory cache otherwise.
"""

from app.db.redis import get_redis
from app.services.cache import Cache, InMemoryBackend, RedisBackend

# Singleton in-memory backend (shared across requests when Redis is not available)
_in_memory_backend: InMemoryBackend | None = None


def _get_in_memory_backend() -> InMemoryBackend:
    """Get or create the singleton in-memory backend."""
    global _in_memory_backend
    if _in_memory_backend is None:
        _in_memory_backend = InMemoryBackend()
    return _in_memory_backend


async def get_cache() -> Cache:
    """Get cache instance with appropriate backend."""
    redis_client = await get_redis()

    if redis_client is not None:
        return Cache(RedisBackend(redis_client))

    # Fall back to in-memory cache
    return Cache(_get_in_memory_backend())


async def get_cache_backend():
    """Get the raw cache backend (for trending service)."""
    redis_client = await get_redis()

    if redis_client is not None:
        return RedisBackend(redis_client)

    return _get_in_memory_backend()
