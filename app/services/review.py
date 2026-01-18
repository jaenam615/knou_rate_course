from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories import CourseRepository, ReviewRepository, TagRepository, UserRepository
from app.schemas import ReviewCreate, ReviewResponse


class ReviewServiceError(Exception):
    pass


class CourseNotFoundError(ReviewServiceError):
    pass


class TagNotFoundError(ReviewServiceError):
    pass


class DuplicateReviewError(ReviewServiceError):
    pass


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.review_repo = ReviewRepository(db)
        self.course_repo = CourseRepository(db)
        self.tag_repo = TagRepository(db)
        self.user_repo = UserRepository(db)

    async def create_review(
        self, course_id: int, user: User, data: ReviewCreate
    ) -> ReviewResponse:
        # Check course exists
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise CourseNotFoundError("Course not found")

        # Check for duplicate review (same user, course)
        existing = await self.review_repo.get_by_user_and_course(user.id, course_id)
        if existing:
            raise DuplicateReviewError("You have already reviewed this course")

        # Validate tags
        if data.tag_ids:
            tags = await self.tag_repo.get_by_ids(data.tag_ids)
            if len(tags) != len(data.tag_ids):
                raise TagNotFoundError("One or more tags not found")

        # Create review
        review = await self.review_repo.create(
            course_id=course_id,
            user_id=user.id,
            rating_overall=data.rating_overall,
            difficulty=data.difficulty,
            workload=data.workload,
            text=data.text,
        )

        # Increment user's review count
        await self.user_repo.update(user, review_count=user.review_count + 1)

        # Add tags
        if data.tag_ids:
            await self.review_repo.add_tags(review.id, data.tag_ids)
            tags_data = [
                {"id": t.id, "name": t.name, "type": t.type}
                for t in await self.tag_repo.get_by_ids(data.tag_ids)
            ]
        else:
            tags_data = []

        return ReviewResponse(
            id=review.id,
            course_id=review.course_id,
            rating_overall=review.rating_overall,
            difficulty=review.difficulty,
            workload=review.workload,
            text=review.text,
            created_at=review.created_at,
            tags=tags_data,
        )
