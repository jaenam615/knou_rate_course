"""
Trending searches service.
Tracks search queries and returns top trending searches with rank changes.
"""

from datetime import datetime, UTC
from typing import Literal

import redis.asyncio as redis


# Redis keys
def _current_period_key() -> str:
    """Key for current hour's searches."""
    hour = datetime.now(UTC).strftime("%Y%m%d%H")
    return f"trending:current:{hour}"


def _previous_period_key() -> str:
    """Key for previous hour's searches (for rank comparison)."""
    hour = datetime.now(UTC).hour - 1
    if hour < 0:
        hour = 23
    date = datetime.now(UTC).strftime("%Y%m%d")
    return f"trending:current:{date}{hour:02d}"


TRENDING_CACHE_KEY = "trending:cached"
TRENDING_CACHE_TTL = 300  # 5 minutes


class TrendingService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def log_search(self, query: str) -> None:
        """Log a search query for trending tracking."""
        if not query or len(query) < 2:
            return

        query = query.strip().lower()
        key = _current_period_key()

        # Increment score in sorted set
        await self.redis.zincrby(key, 1, query)
        # Set expiry (2 hours to keep previous period for comparison)
        await self.redis.expire(key, 7200)

    async def get_trending(self, limit: int = 10) -> list[dict]:
        """
        Get trending searches with rank changes.
        Returns cached result if available.
        """
        # Check cache first
        cached = await self.redis.get(TRENDING_CACHE_KEY)
        if cached:
            import json
            return json.loads(cached)

        # Get current top searches
        current_key = _current_period_key()
        previous_key = _previous_period_key()

        # Get top N from current period
        current_top = await self.redis.zrevrange(current_key, 0, limit - 1, withscores=True)

        if not current_top:
            return []

        # Get previous period rankings for comparison
        previous_ranks = {}
        previous_top = await self.redis.zrevrange(previous_key, 0, 49, withscores=True)
        for rank, (name, _) in enumerate(previous_top, 1):
            previous_ranks[name] = rank

        # Build response with rank changes
        result = []
        for rank, (name, score) in enumerate(current_top, 1):
            prev_rank = previous_ranks.get(name)

            if prev_rank is None:
                change: Literal["up", "down", "same", "new"] = "new"
                change_amount = 0
            elif prev_rank > rank:
                change = "up"
                change_amount = prev_rank - rank
            elif prev_rank < rank:
                change = "down"
                change_amount = rank - prev_rank
            else:
                change = "same"
                change_amount = 0

            result.append({
                "rank": rank,
                "name": name,
                "change": change,
                "changeAmount": change_amount,
            })

        # Cache result
        import json
        await self.redis.setex(TRENDING_CACHE_KEY, TRENDING_CACHE_TTL, json.dumps(result))

        return result
