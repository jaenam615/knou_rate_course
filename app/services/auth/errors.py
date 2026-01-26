class AuthServiceError(Exception):
    status_code = 400
    message = "Authentication service error"

    def __init__(self, message: str | None = None):
        super().__init__(message or self.message)


class InvalidEmailDomainError(AuthServiceError):
    pass


class EmailAlreadyExistsError(AuthServiceError):
    pass


class InvalidCredentialsError(AuthServiceError):
    pass


class EmailNotVerifiedError(AuthServiceError):
    pass


class InvalidVerificationTokenError(AuthServiceError):
    pass


class VerificationTokenExpiredError(AuthServiceError):
    pass


class AccountDeletedError(AuthServiceError):
    pass
