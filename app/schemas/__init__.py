from app.schemas.major import MajorResponse
from app.schemas.course import CourseResponse, CourseListResponse, CourseDetailResponse
from app.schemas.review import ReviewResponse, ReviewCreate
from app.schemas.tag import TagResponse
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
    VerifyEmailRequest,
    ResendVerificationRequest,
)
from app.schemas.search import SearchResult, TrendingItem

__all__ = [
    "MajorResponse",
    "CourseResponse",
    "CourseListResponse",
    "CourseDetailResponse",
    "ReviewResponse",
    "ReviewCreate",
    "TagResponse",
    "SignupRequest",
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "MessageResponse",
    "VerifyEmailRequest",
    "ResendVerificationRequest",
    "SearchResult",
    "TrendingItem",
]
