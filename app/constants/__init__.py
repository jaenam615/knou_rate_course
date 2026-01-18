"""
Centralized constants for the application.

Usage:
    from app.constants import AuthConstants, CacheTTL, RateLimits

    # Or import specific modules
    from app.constants.auth import AuthConstants
    from app.constants.validation import ReviewValidation
"""

from app.constants.auth import AuthConstants
from app.constants.cache import CacheKeys, CacheTTL
from app.constants.course import CourseStatus
from app.constants.rate_limit import RateLimits
from app.constants.review import ReviewConstants
from app.constants.validation import (
    CourseValidation,
    PaginationDefaults,
    ReviewValidation,
    SearchValidation,
)

__all__ = [
    # Auth
    "AuthConstants",
    # Cache
    "CacheTTL",
    "CacheKeys",
    # Course
    "CourseStatus",
    # Rate Limit
    "RateLimits",
    # Review
    "ReviewConstants",
    # Validation
    "ReviewValidation",
    "CourseValidation",
    "SearchValidation",
    "PaginationDefaults",
]
