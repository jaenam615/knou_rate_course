from pydantic import BaseModel

from app.schemas.major import MajorResponse
from app.schemas.review import ReviewResponse


class CourseResponse(BaseModel):
    id: int
    course_code: str
    name: str
    credits: int
    is_archived: bool
    major_id: int

    class Config:
        from_attributes = True


class CourseListResponse(BaseModel):
    id: int
    course_code: str
    name: str
    credits: int
    major_name: str
    avg_rating: float | None = None
    avg_difficulty: float | None = None
    avg_workload: float | None = None
    review_count: int = 0


class CourseDetailResponse(BaseModel):
    id: int
    course_code: str
    name: str
    credits: int
    is_archived: bool
    major: MajorResponse
    avg_rating: float | None = None
    avg_difficulty: float | None = None
    avg_workload: float | None = None
    review_count: int = 0
    reviews: list[ReviewResponse] = []
