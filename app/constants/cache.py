"""Cache and Redis-related constants."""


class CacheTTL:
    """Time-to-live values in seconds."""

    # General cache
    DEFAULT = 300  # 5 minutes

    # Trending
    TRENDING_DATA = 60 * 60 * 24  # 24 hours
    TRENDING_RESPONSE = 120  # 2 minutes


class CacheKeys:
    """Redis key prefixes and patterns."""

    TRENDING_24H = "trending:24h"
    TRENDING_CACHED_PREFIX = "trending:cached:24h"
