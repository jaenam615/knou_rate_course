"""Rate limiting constants."""


class RateLimits:
    """Rate limit values in 'count/period' format for slowapi."""

    AUTH = "5/minute"  # Signup, login, verification
    WRITE = "10/minute"  # Create review, etc.
    SEARCH = "30/minute"  # Search endpoints
    DEFAULT = "60/minute"  # General API endpoints
