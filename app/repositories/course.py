from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Course, Major, Review
from app.repositories.base import BaseRepository


class CourseRepository(BaseRepository[Course]):
    def __init__(self, db: AsyncSession):
        super().__init__(Course, db)

    async def get_list_with_stats(
        self,
        major_id: int | None = None,
        q: str | None = None,
        sort: str = "top_rated",
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        review_stats = (
            select(
                Review.course_id,
                func.avg(Review.rating_overall).label("avg_rating"),
                func.avg(Review.difficulty).label("avg_difficulty"),
                func.avg(Review.workload).label("avg_workload"),
                func.count(Review.id).label("review_count"),
                func.max(Review.created_at).label("latest_review"),
            )
            .where(Review.is_hidden == False)
            .group_by(Review.course_id)
            .subquery()
        )

        query = (
            select(
                Course.id,
                Course.course_code,
                Course.name,
                Major.name.label("major_name"),
                review_stats.c.avg_rating,
                review_stats.c.avg_difficulty,
                review_stats.c.avg_workload,
                func.coalesce(review_stats.c.review_count, 0).label("review_count"),
            )
            .join(Major, Course.major_id == Major.id)
            .outerjoin(review_stats, Course.id == review_stats.c.course_id)
            .where(Course.is_archived == False)
        )

        if major_id:
            query = query.where(Course.major_id == major_id)
        if q:
            query = query.where(Course.name.ilike(f"%{q}%"))

        if sort == "top_rated":
            query = query.order_by(review_stats.c.avg_rating.desc().nullslast())
        elif sort == "most_reviewed":
            query = query.order_by(review_stats.c.review_count.desc().nullslast())
        elif sort == "latest":
            query = query.order_by(review_stats.c.latest_review.desc().nullslast())

        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        return [
            {
                "id": row.id,
                "course_code": row.course_code,
                "name": row.name,
                "major_name": row.major_name,
                "avg_rating": (
                    round(float(row.avg_rating), 2) if row.avg_rating else None
                ),
                "avg_difficulty": (
                    round(float(row.avg_difficulty), 2) if row.avg_difficulty else None
                ),
                "avg_workload": (
                    round(float(row.avg_workload), 2) if row.avg_workload else None
                ),
                "review_count": row.review_count,
            }
            for row in result.all()
        ]

    async def get_detail_with_stats(self, course_id: int) -> dict | None:
        # Get course with major
        result = await self.db.execute(
            select(Course)
            .options(selectinload(Course.major))
            .where(Course.id == course_id)
        )
        course = result.scalar_one_or_none()
        if not course:
            return None

        # Get review stats
        stats_result = await self.db.execute(
            select(
                func.avg(Review.rating_overall).label("avg_rating"),
                func.avg(Review.difficulty).label("avg_difficulty"),
                func.avg(Review.workload).label("avg_workload"),
                func.count(Review.id).label("review_count"),
            )
            .where(Review.course_id == course_id)
            .where(Review.is_hidden == False)
        )
        stats = stats_result.one()

        return {
            "course": course,
            "avg_rating": (
                round(float(stats.avg_rating), 2) if stats.avg_rating else None
            ),
            "avg_difficulty": (
                round(float(stats.avg_difficulty), 2) if stats.avg_difficulty else None
            ),
            "avg_workload": (
                round(float(stats.avg_workload), 2) if stats.avg_workload else None
            ),
            "review_count": stats.review_count or 0,
        }
