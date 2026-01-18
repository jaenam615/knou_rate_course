import json
from typing import Awaitable, Callable, TypeVar

import redis.asyncio as redis

from app.constants.cache_constants import CacheConstants

T = TypeVar("T")


class RedisCache:
    def __init__(self, client: redis.Redis):
        self.client = client

    async def get_or_set_json(
        self,
        key: str,
        loader: Callable[[], Awaitable[T]],
        ttl: int = CacheConstants.DEFAULT_TIMEOUT,
    ) -> T:
        cached = await self.client.get(key)
        if cached is not None:
            return json.loads(cached)

        value = await loader()
        await self.client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
        return value

    async def delete(self, key: str) -> None:
        await self.client.delete(key)
