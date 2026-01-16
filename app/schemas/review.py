from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.tag import TagResponse


class ReviewCreate(BaseModel):
    year: int = Field(..., ge=2000, le=2100)
    semester: int = Field(..., ge=1, le=2)
    rating_overall: int = Field(..., ge=1, le=5)
    difficulty: int = Field(..., ge=1, le=5)
    workload: int = Field(..., ge=1, le=5)
    text: str = Field(..., min_length=10, max_length=2000)
    tag_ids: list[int] = Field(default_factory=list)


class ReviewResponse(BaseModel):
    id: int
    course_id: int
    year: int
    semester: int
    rating_overall: int
    difficulty: int
    workload: int
    text: str
    created_at: datetime
    tags: list[TagResponse] = []

    class Config:
        from_attributes = True
