from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import CourseRepository, ReviewRepository
from app.schemas import CourseListResponse, CourseDetailResponse


class CourseService:
    def __init__(self, db: AsyncSession):
        self.course_repo = CourseRepository(db)
        self.review_repo = ReviewRepository(db)

    async def get_list(
        self,
        major_id: int | None = None,
        q: str | None = None,
        sort: str = "top_rated",
        limit: int = 20,
        offset: int = 0,
    ) -> list[CourseListResponse]:
        rows = await self.course_repo.get_list_with_stats(
            major_id=major_id, q=q, sort=sort, limit=limit, offset=offset
        )
        return [CourseListResponse(**row) for row in rows]

    async def get_detail(self, course_id: int) -> CourseDetailResponse | None:
        data = await self.course_repo.get_detail_with_stats(course_id)
        if not data:
            return None

        course = data["course"]
        reviews = await self.review_repo.get_by_course_id(course_id)

        reviews_data = []
        for review in reviews:
            reviews_data.append(
                {
                    "id": review.id,
                    "course_id": review.course_id,
                    "year": review.year,
                    "semester": review.semester,
                    "rating_overall": review.rating_overall,
                    "difficulty": review.difficulty,
                    "workload": review.workload,
                    "text": review.text,
                    "created_at": review.created_at,
                    "tags": [
                        {"id": rt.tag.id, "name": rt.tag.name, "type": rt.tag.type}
                        for rt in review.tags
                    ],
                }
            )

        return CourseDetailResponse(
            id=course.id,
            course_code=course.course_code,
            name=course.name,
            credits=course.credits,
            is_archived=course.is_archived,
            major={"id": course.major.id, "name": course.major.name},
            avg_rating=data["avg_rating"],
            avg_difficulty=data["avg_difficulty"],
            avg_workload=data["avg_workload"],
            review_count=data["review_count"],
            reviews=reviews_data,
        )
