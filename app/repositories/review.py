from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Review, ReviewTag
from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    def __init__(self, db: AsyncSession):
        super().__init__(Review, db)

    async def get_by_course_id(self, course_id: int) -> list[Review]:
        result = await self.db.execute(
            select(Review)
            .options(selectinload(Review.tags).selectinload(ReviewTag.tag))
            .where(Review.course_id == course_id)
            .where(Review.is_hidden.is_(False))
            .order_by(Review.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_user_and_course(
        self, user_id: int, course_id: int
    ) -> Review | None:
        """Check if user already has a review for this course."""
        result = await self.db.execute(
            select(Review)
            .where(Review.user_id == user_id)
            .where(Review.course_id == course_id)
        )
        return result.scalar_one_or_none()

    async def add_tags(self, review_id: int, tag_ids: list[int]) -> None:
        for tag_id in tag_ids:
            review_tag = ReviewTag(review_id=review_id, tag_id=tag_id)
            self.db.add(review_tag)
        await self.db.flush()
