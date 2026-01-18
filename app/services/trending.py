import json

from app.services.cache import RedisCache

TRENDING_24H_KEY = "trending:24h"
TRENDING_24H_TTL = 60 * 60 * 24
TRENDING_RESPONSE_CACHE_TTL = 120


class TrendingService:
    def __init__(self, cache: RedisCache):
        self._cache = cache

    async def log_search(self, query: str) -> None:
        if not query:
            return

        query = query.strip().lower()
        if len(query) < 2:
            return
        if len(query) > 50:
            return

        await self._cache.client.zincrby(TRENDING_24H_KEY, 1, query)
        await self._cache.client.expire(TRENDING_24H_KEY, TRENDING_24H_TTL)

    async def get_trending(self, limit: int = 10) -> list[dict]:
        limit = max(1, min(limit, 50))

        cache_key = f"trending:cached:24h:limit={limit}"

        cached = await self._cache.client.get(cache_key)
        if cached:
            return json.loads(cached)

        top = await self._cache.client.zrevrange(
            TRENDING_24H_KEY, 0, limit - 1, withscores=True
        )

        result = [
            {"rank": i + 1, "name": name, "count": int(score)}
            for i, (name, score) in enumerate(top)
        ]

        await self._cache.client.setex(
            cache_key,
            TRENDING_RESPONSE_CACHE_TTL,
            json.dumps(result, ensure_ascii=False),
        )
        return result
