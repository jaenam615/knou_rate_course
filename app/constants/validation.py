"""Validation constants for request/response schemas."""


class ReviewValidation:
    # Rating ranges (1-5 scale)
    RATING_MIN = 1
    RATING_MAX = 5

    # Review text limits
    TEXT_MIN_LENGTH = 10
    TEXT_MAX_LENGTH = 2000


class CourseValidation:
    # Semester values
    SEMESTER_MIN = 1
    SEMESTER_MAX = 2

    # Grade levels (학년)
    GRADE_MIN = 1
    GRADE_MAX = 4


class SearchValidation:
    # Search query limits
    QUERY_MIN_LENGTH = 2
    QUERY_MAX_LENGTH = 100


class PaginationDefaults:
    # Course list
    COURSE_LIST_DEFAULT_LIMIT = 20
    COURSE_LIST_MAX_LIMIT = 100

    # Search results
    SEARCH_DEFAULT_LIMIT = 20
    SEARCH_MAX_LIMIT = 50

    # Trending
    TRENDING_DEFAULT_LIMIT = 10
    TRENDING_MAX_LIMIT = 20
