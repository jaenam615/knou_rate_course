from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import CourseListResponse, CourseDetailResponse
from app.services import CourseService

router = APIRouter()


class SortOption(str, Enum):
    TOP_RATED = "top_rated"
    MOST_REVIEWED = "most_reviewed"
    LATEST = "latest"


@router.get("", response_model=list[CourseListResponse])
async def get_courses(
    db: AsyncSession = Depends(get_db),
    major_id: Annotated[int | None, Query(description="Filter by major")] = None,
    q: Annotated[str | None, Query(description="Search query")] = None,
    sort: Annotated[SortOption, Query(description="Sort option")] = SortOption.TOP_RATED,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CourseListResponse]:
    service = CourseService(db)
    return await service.get_list(
        major_id=major_id, q=q, sort=sort.value, limit=limit, offset=offset
    )


@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
) -> CourseDetailResponse:
    service = CourseService(db)
    result = await service.get_detail(course_id)

    if not result:
        raise HTTPException(status_code=404, detail="Course not found")

    return result
