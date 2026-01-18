from app.db.redis import get_redis
from app.services.cache import RedisCache


async def get_cache() -> RedisCache:
    redis_client = await get_redis()
    return RedisCache(redis_client)
