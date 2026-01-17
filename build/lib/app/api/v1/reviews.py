from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils import CurrentUser
from app.db import get_db
from app.schemas import ReviewCreate, ReviewResponse
from app.services import ReviewService
from app.services.review import (
    CourseNotFoundError,
    TagNotFoundError,
    DuplicateReviewError,
)

router = APIRouter()


@router.post(
    "/courses/{course_id}/reviews", response_model=ReviewResponse, status_code=201
)
async def create_review(
    course_id: int,
    review_data: ReviewCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    service = ReviewService(db)

    try:
        return await service.create_review(course_id, current_user, review_data)
    except CourseNotFoundError:
        raise HTTPException(status_code=404, detail="Course not found")
    except TagNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateReviewError as e:
        raise HTTPException(status_code=409, detail=str(e))
