from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps.cache import get_cache
from app.repositories import CourseRepository
from app.schemas import CourseDetailResponse, CourseEvalSummary, CourseListResponse
from app.services import CourseService
from app.services.cache import RedisCache
from app.utils import CurrentUser, OptionalCurrentUser

router = APIRouter()


class SortOption(str, Enum):
    TOP_RATED = "top_rated"
    MOST_REVIEWED = "most_reviewed"
    LATEST = "latest"


@router.get("", response_model=list[CourseListResponse])
async def get_courses(
    current_user: OptionalCurrentUser,
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache),
    major_id: Annotated[int | None, Query(description="Filter by major")] = None,
    q: Annotated[str | None, Query(description="Search query")] = None,
    sort: Annotated[
        SortOption, Query(description="Sort option")
    ] = SortOption.TOP_RATED,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CourseListResponse]:
    service = CourseService(db=db, cache=cache)
    return await service.get_list(
        user=current_user,
        major_id=major_id,
        q=q,
        sort=sort.value,
        limit=limit,
        offset=offset,
    )


@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course(
    course_id: int,
    current_user: OptionalCurrentUser,
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache),
) -> CourseDetailResponse:
    service = CourseService(db=db, cache=cache)
    result = await service.get_detail(course_id, current_user)

    if not result:
        raise HTTPException(status_code=404, detail="Course not found")

    return result


@router.get("/{course_id}/eval-summary", response_model=CourseEvalSummary)
async def get_course_eval_summary(
    course_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> CourseEvalSummary:
    """
    Get aggregated evaluation method summary for a course.
    Shows dominant final type and whether midterm/attendance are common.
    """
    repo = CourseRepository(db)

    # Check course exists
    course = await repo.get_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    result = await repo.get_eval_summary(course_id)
    return CourseEvalSummary(**result)
