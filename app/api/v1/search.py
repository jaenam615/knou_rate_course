"""
Search and Trending API endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.db.redis import get_redis
from app.deps.cache import get_cache
from app.repositories import CourseRepository
from app.schemas import SearchResult, TrendingItem
from app.services.cache import RedisCache
from app.services.trending import TrendingService
from app.utils import CurrentUser

router = APIRouter()


@router.get("/search", response_model=list[SearchResult])
async def search_courses(
    current_user: CurrentUser,
    q: Annotated[str, Query(min_length=2, max_length=100, description="Search query")],
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache),
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> list[SearchResult]:
    """
    Search courses by name.
    Also logs the search query for trending tracking.
    """
    try:
        await TrendingService(cache=cache).log_search(q)
    except Exception:
        pass

    results = await CourseRepository(db).search(q, limit=limit)
    return [SearchResult(**r) for r in results]


@router.get("/trending", response_model=list[TrendingItem])
async def get_trending(
    cache=Depends(get_cache),
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> list[TrendingItem]:
    trending_service = TrendingService(cache)
    results = await trending_service.get_trending(limit=limit)
    return [TrendingItem(**r) for r in results]
