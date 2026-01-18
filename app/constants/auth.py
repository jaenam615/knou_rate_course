"""Authentication-related constants."""


class AuthConstants:
    # Email validation
    KNOU_EMAIL_DOMAIN = "@knou.ac.kr"

    # Verification token
    VERIFICATION_TOKEN_EXPIRY_HOURS = 24

    # Password requirements
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 100

    # Access control
    REQUIRED_REVIEWS_FOR_FULL_ACCESS = 3
