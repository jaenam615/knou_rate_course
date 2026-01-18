"""
Search and Trending API endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.db.redis import get_redis
from app.repositories import CourseRepository
from app.schemas import SearchResult, TrendingItem
from app.services.trending import TrendingService
from app.utils import CurrentUser

router = APIRouter()


@router.get("/search", response_model=list[SearchResult])
async def search_courses(
    current_user: CurrentUser,
    q: Annotated[str, Query(min_length=2, max_length=100, description="Search query")],
    db: AsyncSession = Depends(get_db),
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> list[SearchResult]:
    """
    Search courses by name.
    Also logs the search query for trending tracking.
    """
    # Log search for trending (fire and forget)
    try:
        redis = await get_redis()
        trending_service = TrendingService(redis)
        await trending_service.log_search(q)
    except Exception:
        pass  # Don't fail the search if Redis is down

    # Perform search
    course_repo = CourseRepository(db)
    results = await course_repo.search(q, limit=limit)
    return [SearchResult(**r) for r in results]


@router.get("/trending", response_model=list[TrendingItem])
async def get_trending(
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> list[TrendingItem]:
    """
    Get trending search terms.
    Returns top searches with rank changes compared to previous period.
    """
    try:
        redis = await get_redis()
        trending_service = TrendingService(redis)
        results = await trending_service.get_trending(limit=limit)
        return [TrendingItem(**r) for r in results]
    except Exception:
        # Return empty list if Redis is down
        return []
