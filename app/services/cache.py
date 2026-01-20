"""
Cache abstraction with Redis and in-memory implementations.

When Redis is not configured, falls back to in-memory cache.
In-memory cache is process-local and cleared on restart.
"""

import json
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Awaitable, Callable, TypeVar

from app.constants import CacheTTL

T = TypeVar("T")


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Get a value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        """Set a value in cache with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        pass

    @abstractmethod
    async def setex(self, key: str, seconds: int, value: str) -> None:
        """Set a value with expiration."""
        pass

    @abstractmethod
    async def zincrby(self, key: str, amount: float, member: str) -> float:
        """Increment score in sorted set."""
        pass

    @abstractmethod
    async def zrevrange(
        self, key: str, start: int, end: int, withscores: bool = False
    ) -> list:
        """Get range from sorted set in reverse order."""
        pass

    @abstractmethod
    async def expire(self, key: str, seconds: int) -> None:
        """Set expiration on key."""
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Check if cache is available."""
        pass


class RedisBackend(CacheBackend):
    """Redis-backed cache implementation."""

    def __init__(self, client):
        self.client = client

    async def get(self, key: str) -> str | None:
        return await self.client.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        await self.client.set(key, value, ex=ex)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def setex(self, key: str, seconds: int, value: str) -> None:
        await self.client.setex(key, seconds, value)

    async def zincrby(self, key: str, amount: float, member: str) -> float:
        return await self.client.zincrby(key, amount, member)

    async def zrevrange(
        self, key: str, start: int, end: int, withscores: bool = False
    ) -> list:
        return await self.client.zrevrange(key, start, end, withscores=withscores)

    async def expire(self, key: str, seconds: int) -> None:
        await self.client.expire(key, seconds)

    async def ping(self) -> bool:
        return await self.client.ping()


class InMemoryBackend(CacheBackend):
    """In-memory cache implementation (process-local, non-persistent)."""

    def __init__(self):
        self._cache: dict[str, tuple[str, float | None]] = {}  # key -> (value, expires_at)
        self._sorted_sets: dict[str, dict[str, float]] = defaultdict(dict)  # key -> {member: score}
        self._expiries: dict[str, float] = {}  # key -> expires_at

    def _is_expired(self, key: str) -> bool:
        if key in self._expiries:
            if time.time() > self._expiries[key]:
                self._cleanup_key(key)
                return True
        return False

    def _cleanup_key(self, key: str) -> None:
        self._cache.pop(key, None)
        self._sorted_sets.pop(key, None)
        self._expiries.pop(key, None)

    async def get(self, key: str) -> str | None:
        if self._is_expired(key):
            return None
        entry = self._cache.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at and time.time() > expires_at:
            del self._cache[key]
            return None
        return value

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        expires_at = time.time() + ex if ex else None
        self._cache[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        self._cleanup_key(key)

    async def setex(self, key: str, seconds: int, value: str) -> None:
        await self.set(key, value, ex=seconds)

    async def zincrby(self, key: str, amount: float, member: str) -> float:
        if self._is_expired(key):
            self._sorted_sets[key] = {}
        current = self._sorted_sets[key].get(member, 0)
        new_score = current + amount
        self._sorted_sets[key][member] = new_score
        return new_score

    async def zrevrange(
        self, key: str, start: int, end: int, withscores: bool = False
    ) -> list:
        if self._is_expired(key):
            return []
        sorted_set = self._sorted_sets.get(key, {})
        sorted_items = sorted(sorted_set.items(), key=lambda x: x[1], reverse=True)
        # Handle negative indices
        if end < 0:
            end = len(sorted_items) + end + 1
        else:
            end = end + 1
        sliced = sorted_items[start:end]
        if withscores:
            return sliced
        return [item[0] for item in sliced]

    async def expire(self, key: str, seconds: int) -> None:
        self._expiries[key] = time.time() + seconds

    async def ping(self) -> bool:
        return True


class Cache:
    """Cache service with backend abstraction."""

    def __init__(self, backend: CacheBackend):
        self.client = backend

    async def get_or_set_json(
        self,
        key: str,
        loader: Callable[[], Awaitable[T]],
        ttl: int = CacheTTL.DEFAULT,
    ) -> T:
        """Get from cache or load and cache the value."""
        cached = await self.client.get(key)
        if cached is not None:
            return json.loads(cached)

        value = await loader()
        await self.client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
        return value

    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        await self.client.delete(key)


# Backwards compatibility alias
RedisCache = Cache
