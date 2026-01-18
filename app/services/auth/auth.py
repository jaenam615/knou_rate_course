import asyncio
import logging
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.constants import AuthConstants
from app.models import User
from app.repositories import UserRepository
from app.services.auth.errors import (
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidEmailDomainError,
    InvalidVerificationTokenError,
    VerificationTokenExpiredError,
)
from app.services.mailer import send_verification_email

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    def _validate_knou_email(self, email: str) -> None:
        if not email.lower().endswith(AuthConstants.KNOU_EMAIL_DOMAIN):
            raise InvalidEmailDomainError(
                f"Email must be a KNOU email address ({AuthConstants.KNOU_EMAIL_DOMAIN})"
            )

    def _hash_password(self, password: str) -> str:
        import bcrypt

        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        import bcrypt

        return bcrypt.checkpw(password.encode(), password_hash.encode())

    def _generate_verification_token(self) -> str:
        return secrets.token_urlsafe(32)

    async def signup(self, email: str, password: str) -> User:
        """
        Register a new user and sends verification email.
        Returns the user.
        """
        user = await self._create_user(email, password)
        try:
            await self._issue_token_and_send(user)
        except Exception:
            logger.exception("Failed to send verification email during signup for %s", email)

        return user

    async def _create_user(self, email: str, password: str) -> User:
        """Create a new user in the database."""
        email = email.lower().strip()
        self._validate_knou_email(email)

        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise EmailAlreadyExistsError("Email already registered")

        token = self._generate_verification_token()
        expires = datetime.now(UTC) + timedelta(hours=AuthConstants.VERIFICATION_TOKEN_EXPIRY_HOURS)

        user = await self.user_repo.create(
            email=email,
            password_hash=self._hash_password(password),
            is_verified=False,
            verification_token=token,
            verification_token_expires=expires,
        )

        return user

    async def resend_verification(self, email: str) -> None:
        user = await self.user_repo.get_by_email(email.lower().strip())
        if not user:
            return
        if user.is_verified:
            return

        await self._issue_token_and_send(user)

    async def _issue_token_and_send(self, user: User) -> None:
        token = self._generate_verification_token()
        expires = datetime.now(UTC) + timedelta(hours=AuthConstants.VERIFICATION_TOKEN_EXPIRY_HOURS)

        await self.user_repo.update(
            instance=user,
            verification_token=token,
            verification_token_expires=expires,
        )

        try:
            await self._send_verification_email(user.email, token)
        except Exception:
            logger.exception("Failed to send verification email to %s", user.email)

    async def _send_verification_email(self, email: str, token: str) -> None:
        verify_url = f"{settings.frontend_url}/verify-email?token={token}"
        await asyncio.to_thread(
            send_verification_email, to_email=email, verify_url=verify_url
        )

    async def verify_email(self, token: str) -> User:
        """Verify user's email with the token."""
        user = await self.user_repo.get_by_verification_token(token)
        if not user:
            raise InvalidVerificationTokenError("Invalid verification token")

        if user.verification_token_expires < datetime.now(UTC):
            raise VerificationTokenExpiredError("Verification token has expired")

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
