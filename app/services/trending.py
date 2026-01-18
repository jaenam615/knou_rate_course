import json

from app.constants import CacheKeys, CacheTTL, SearchValidation
from app.services.cache import RedisCache


class TrendingService:
    def __init__(self, cache: RedisCache):
        self._cache = cache

    async def log_search(self, query: str) -> None:
        if not query:
            return

        query = query.strip().lower()
        if len(query) < SearchValidation.QUERY_MIN_LENGTH:
            return
        if len(query) > 50:
            return

        await self._cache.client.zincrby(CacheKeys.TRENDING_24H, 1, query)
        await self._cache.client.expire(CacheKeys.TRENDING_24H, CacheTTL.TRENDING_DATA)

    async def get_trending(self, limit: int = 10) -> list[dict]:
        limit = max(1, min(limit, 50))

        cache_key = f"{CacheKeys.TRENDING_CACHED_PREFIX}:limit={limit}"

        cached = await self._cache.client.get(cache_key)
        if cached:
            return json.loads(cached)

        top = await self._cache.client.zrevrange(
            CacheKeys.TRENDING_24H, 0, limit - 1, withscores=True
        )

        result = [
            {"rank": i + 1, "name": name, "count": int(score)}
            for i, (name, score) in enumerate(top)
        ]

        await self._cache.client.setex(
            cache_key,
            CacheTTL.TRENDING_RESPONSE,
            json.dumps(result, ensure_ascii=False),
        )
        return result
