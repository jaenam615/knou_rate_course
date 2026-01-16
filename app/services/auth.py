import secrets
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories import UserRepository

KNOU_EMAIL_DOMAIN = "@knou.ac.kr"
VERIFICATION_TOKEN_EXPIRY_HOURS = 24


class AuthServiceError(Exception):
    pass


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


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    def _validate_knou_email(self, email: str) -> None:
        if not email.lower().endswith(KNOU_EMAIL_DOMAIN):
            raise InvalidEmailDomainError(
                f"Email must be a KNOU email address ({KNOU_EMAIL_DOMAIN})"
            )

    def _hash_password(self, password: str) -> str:
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        import bcrypt
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    def _generate_verification_token(self) -> str:
        return secrets.token_urlsafe(32)

    async def signup(self, email: str, password: str) -> tuple[User, str]:
        """
        Register a new user. Returns the user and verification token.
        The caller should send the verification email.
        """
        email = email.lower().strip()
        self._validate_knou_email(email)

        # Check if email already exists
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise EmailAlreadyExistsError("Email already registered")

        # Generate verification token
        token = self._generate_verification_token()
        expires = datetime.utcnow() + timedelta(hours=VERIFICATION_TOKEN_EXPIRY_HOURS)

        # Create user
        user = await self.user_repo.create(
            email=email,
            password_hash=self._hash_password(password),
            is_verified=False,
            verification_token=token,
            verification_token_expires=expires,
        )

        return user, token

    async def verify_email(self, token: str) -> User:
        """Verify user's email with the token."""
        user = await self.user_repo.get_by_verification_token(token)
        if not user:
            raise InvalidVerificationTokenError("Invalid verification token")

        if user.verification_token_expires < datetime.utcnow():
            raise VerificationTokenExpiredError("Verification token has expired")

        # Update user
        await self.user_repo.update(
            user,
            is_verified=True,
            verification_token=None,
            verification_token_expires=None,
        )

        return user

    async def login(self, email: str, password: str) -> User:
        """Authenticate user and return user object."""
        email = email.lower().strip()

        user = await self.user_repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsError("Invalid email or password")

        if not self._verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_verified:
            raise EmailNotVerifiedError("Email not verified. Please check your email.")

        return user

    async def resend_verification(self, email: str) -> tuple[User, str]:
        """Resend verification email. Returns user and new token."""
        email = email.lower().strip()

        user = await self.user_repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsError("Email not found")

        if user.is_verified:
            raise AuthServiceError("Email already verified")

        # Generate new token
        token = self._generate_verification_token()
        expires = datetime.utcnow() + timedelta(hours=VERIFICATION_TOKEN_EXPIRY_HOURS)

        await self.user_repo.update(
            user,
            verification_token=token,
            verification_token_expires=expires,
        )

        return user, token
