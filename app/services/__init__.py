from app.services.auth.auth import AuthService
from app.services.course import CourseService
from app.services.major import MajorService
from app.services.review import ReviewService
from app.services.tag import TagService

__all__ = [
    "MajorService",
    "CourseService",
    "ReviewService",
    "TagService",
    "AuthService",
]
