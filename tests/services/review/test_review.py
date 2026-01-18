"""Unit tests for ReviewService."""

from unittest.mock import AsyncMock

import pytest

from app.models import Course, Review, User
from app.schemas import ReviewCreate
from app.services.review.errors import (
    CourseNotFoundError,
    DuplicateReviewError,
    InvalidReviewTextError,
)
from app.services.review.review import ReviewService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def review_service(mock_db):
    service = ReviewService(mock_db)
    service.review_repo = AsyncMock()
    service.course_repo = AsyncMock()
    service.tag_repo = AsyncMock()
    service.user_repo = AsyncMock()
    return service


@pytest.fixture
def sample_user():
    return User(
        id=1,
        email="test@knou.ac.kr",
        password_hash="x",
        is_verified=True,
        review_count=0,
    )


@pytest.fixture
def sample_course():
    return Course(
        id=1,
        major_id=1,
        course_code="CS101",
        name="컴퓨터개론",
        is_archived=False,
    )


@pytest.fixture
def sample_review_data():
    return ReviewCreate(
        rating_overall=5,
        difficulty=3,
        workload=3,
        text="좋은 강의입니다. 추천합니다!",
        tag_ids=[],
    )


class TestCreateReview:
    @pytest.mark.asyncio
    async def test_create_review_success(
        self, review_service, sample_user, sample_course, sample_review_data
    ):
        review_service.course_repo.get_by_id.return_value = sample_course
        review_service.review_repo.get_by_user_and_course.return_value = None
        review_service.review_repo.create.return_value = Review(
            id=1,
            course_id=1,
            user_id=1,
            rating_overall=5,
            difficulty=3,
            workload=3,
            text="좋은 강의입니다. 추천합니다!",
            tags=[],
        )
        review_service.user_repo.increment_review_count = AsyncMock()

        result = await review_service.create_review(
            course_id=1,
            user=sample_user,
            data=sample_review_data,
        )

        assert result.rating_overall == 5
        review_service.review_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_course_not_found(
        self, review_service, sample_user, sample_review_data
    ):
        review_service.course_repo.get_by_id.return_value = None

        with pytest.raises(CourseNotFoundError):
            await review_service.create_review(
                course_id=999,
                user=sample_user,
                data=sample_review_data,
            )

    @pytest.mark.asyncio
    async def test_create_review_duplicate(
        self, review_service, sample_user, sample_course, sample_review_data
    ):
        review_service.course_repo.get_by_id.return_value = sample_course
        review_service.review_repo.get_by_user_and_course.return_value = Review(
            id=1,
            course_id=1,
            user_id=1,
            rating_overall=4,
            difficulty=3,
            workload=3,
            text="기존 리뷰",
        )

        with pytest.raises(DuplicateReviewError):
            await review_service.create_review(
                course_id=1,
                user=sample_user,
                data=sample_review_data,
            )

    @pytest.mark.asyncio
    async def test_create_review_profanity_rejected(
        self, review_service, sample_user, sample_course
    ):
        review_service.course_repo.get_by_id.return_value = sample_course
        review_service.review_repo.get_by_user_and_course.return_value = None

        bad_review = ReviewCreate(
            rating_overall=1,
            difficulty=5,
            workload=5,
            text="이 수업 시발 진짜 최악임",
            tag_ids=[],
        )

        with pytest.raises(InvalidReviewTextError):
            await review_service.create_review(
                course_id=1,
                user=sample_user,
                data=bad_review,
            )
