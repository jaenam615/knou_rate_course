from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import RATE_LIMIT_WRITE, limiter
from app.db import get_db
from app.schemas import ReviewCreate, ReviewResponse
from app.services import ReviewService
from app.services.review.errors import (
    CourseNotFoundError,
    DuplicateReviewError,
    InvalidReviewTextError,
    TagNotFoundError,
)
from app.utils import CurrentUser

router = APIRouter()


@router.post(
    "/courses/{course_id}/reviews", response_model=ReviewResponse, status_code=201
)
@limiter.limit(RATE_LIMIT_WRITE)
async def create_review(
    request: Request,
    course_id: int,
    review_data: ReviewCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    service = ReviewService(db)

    try:
        return await service.create_review(course_id, current_user, review_data)
    except InvalidReviewTextError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CourseNotFoundError:
        raise HTTPException(status_code=404, detail="Course not found")
    except TagNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateReviewError as e:
        raise HTTPException(status_code=409, detail=str(e))
