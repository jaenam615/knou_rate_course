from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    ResendVerificationRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.schemas.course import (
    CourseDetailResponse,
    CourseEvalSummary,
    CourseListResponse,
    CourseResponse,
)
from app.schemas.major import MajorResponse
from app.schemas.review import ReviewCreate, ReviewResponse
from app.schemas.search import SearchResult, TrendingItem
from app.schemas.tag import TagResponse

__all__ = [
    "MajorResponse",
    "CourseResponse",
    "CourseListResponse",
    "CourseDetailResponse",
    "CourseEvalSummary",
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
