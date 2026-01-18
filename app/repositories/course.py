from sqlalchemy import case, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Course, Major, Review, ReviewTag, Tag
from app.repositories.base import BaseRepository

# Threshold for eval summary (need more than this many reviews to count)
EVAL_TAG_THRESHOLD = 3


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

    async def search(self, q: str, limit: int = 20) -> list[dict]:
        """
        Simple search for courses by name.
        Returns minimal data for search results.
        """
        query = (
            select(
                Course.id,
                Course.course_code,
                Course.name,
                Major.name.label("major_name"),
            )
            .join(Major, Course.major_id == Major.id)
            .where(Course.is_archived == False)
            .where(Course.name.ilike(f"%{q}%"))
            .order_by(Course.name)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return [
            {
                "id": row.id,
                "course_code": row.course_code,
                "name": row.name,
                "major_name": row.major_name,
            }
            for row in result.all()
        ]

    async def get_eval_summary(self, course_id: int) -> dict:
        """
        Get aggregated evaluation method summary for a course.
        Returns which final type is dominant and whether midterm/attendance exist.
        """
        # Count each tag type
        final_exam_count = func.sum(
            case((Tag.name == "기말시험", 1), else_=0)
        )
        final_assignment_count = func.sum(
            case((Tag.name == "기말과제물", 1), else_=0)
        )
        midterm_count = func.sum(
            case((Tag.name == "중간과제물", 1), else_=0)
        )
        attendance_count = func.sum(
            case((Tag.name == "출석수업과제", 1), else_=0)
        )

        query = (
            select(
                final_exam_count.label("final_exam_count"),
                final_assignment_count.label("final_assignment_count"),
                midterm_count.label("midterm_count"),
                attendance_count.label("attendance_count"),
            )
            .select_from(Review)
            .outerjoin(ReviewTag, Review.id == ReviewTag.review_id)
            .outerjoin(Tag, ReviewTag.tag_id == Tag.id)
            .where(Review.course_id == course_id)
            .where(Review.is_hidden == False)
        )

        result = await self.db.execute(query)
        row = result.one()

        final_exam = row.final_exam_count or 0
        final_assignment = row.final_assignment_count or 0
        midterm = row.midterm_count or 0
        attendance = row.attendance_count or 0

        # Determine final type (winner between 기말시험 vs 기말과제물)
        if final_exam > final_assignment:
            final_type = "기말시험"
        elif final_assignment > 0:
            final_type = "기말과제물"
        else:
            final_type = None

        return {
            "final_type": final_type,
            "has_midterm": midterm > EVAL_TAG_THRESHOLD,
            "has_attendance": attendance > EVAL_TAG_THRESHOLD,
        }
