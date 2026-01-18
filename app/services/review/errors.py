class ReviewServiceError(Exception):
    pass


class InvalidReviewTextError(ReviewServiceError):
    pass


class CourseNotFoundError(ReviewServiceError):
    pass


class TagNotFoundError(ReviewServiceError):
    pass


class DuplicateReviewError(ReviewServiceError):
    pass
