from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import CacheTTL
from app.models import User
from app.repositories import CourseRepository, ReviewRepository
from app.schemas import (CourseDetailResponse, CourseListResponse,
                         MajorResponse, ReviewResponse, TagResponse)
from app.services.cache import RedisCache


class CourseService:
    def __init__(self, db: AsyncSession, cache: RedisCache):
        self.course_repo = CourseRepository(db)
        self.review_repo = ReviewRepository(db)
        self.cache = cache

    async def get_list(
        self,
        user: User,
        major_id: int | None = None,
        q: str | None = None,
        sort: str = "top_rated",
        limit: int = 20,
        offset: int = 0,
    ) -> list[CourseListResponse]:
        should_cache = not q

        async def _load_course_list() -> list[dict]:
            return await self.course_repo.get_list_with_stats(
                major_id=major_id,
                q=q,
                sort=sort,
                limit=limit,
                offset=offset,
            )

        if not should_cache:
            rows = await _load_course_list()
        else:
            try:
                major_key = major_id if major_id is not None else "all"
                key = f"courses:list:v1:major={major_key}:sort={sort}:limit={limit}:offset={offset}"
                rows = await self.cache.get_or_set_json(
                    key=key,
                    ttl=CacheTTL.DEFAULT,
                    loader=_load_course_list,
                )
            except Exception:
                rows = await _load_course_list()

        if user.has_full_access:
            return [CourseListResponse(**row) for row in rows]

        return [
            CourseListResponse(
                id=row["id"],
                course_code=row["course_code"],
                name=row["name"],
                major_name=row["major_name"],
                avg_rating=None,
                avg_difficulty=None,
                avg_workload=None,
                review_count=row["review_count"],
            )
            for row in rows
        ]

    async def get_detail(
        self, course_id: int, user: User
    ) -> CourseDetailResponse | None:
        data = await self.course_repo.get_detail_with_stats(course_id)
        if not data:
            return None

        course = data["course"]

        base_response = {
            "id": course.id,
            "course_code": course.course_code,
            "name": course.name,
            "is_archived": course.is_archived,
            "major": MajorResponse(
                id=course.major.id,
                name=course.major.name,
                department=course.major.department,
            ),
            "review_count": data["review_count"],
        }

        if not user.has_full_access:
            return CourseDetailResponse(
                **base_response,
                avg_rating=None,
                avg_difficulty=None,
                avg_workload=None,
                reviews=[],
            )

        reviews = await self.review_repo.get_by_course_id(course_id)
        reviews_data = [
            ReviewResponse(
                id=review.id,
                course_id=review.course_id,
                rating_overall=review.rating_overall,
                difficulty=review.difficulty,
                workload=review.workload,
                text=review.text,
                created_at=review.created_at,
                tags=[
                    TagResponse(id=rt.tag.id, name=rt.tag.name, type=rt.tag.type)
                    for rt in review.tags
                ],
            )
            for review in reviews
        ]

        return CourseDetailResponse(
            **base_response,
            avg_rating=data["avg_rating"],
            avg_difficulty=data["avg_difficulty"],
            avg_workload=data["avg_workload"],
            reviews=reviews_data,
        )
