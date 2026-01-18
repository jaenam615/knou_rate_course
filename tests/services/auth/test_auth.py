"""Unit tests for AuthService."""

from unittest.mock import AsyncMock, patch

import pytest

from app.models import User
from app.services.auth.auth import AuthService
from app.services.auth.errors import (
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidEmailDomainError,
)


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def auth_service(mock_db):
    service = AuthService(mock_db)
    service.user_repo = AsyncMock()
    return service


class TestValidateKnouEmail:
    def test_valid_knou_email(self, auth_service):
        auth_service._validate_knou_email("student@knou.ac.kr")

    def test_invalid_email_domain(self, auth_service):
        with pytest.raises(InvalidEmailDomainError):
            auth_service._validate_knou_email("student@gmail.com")

    def test_case_insensitive(self, auth_service):
        auth_service._validate_knou_email("student@KNOU.AC.KR")


class TestPasswordHashing:
    def test_hash_password(self, auth_service):
        hashed = auth_service._hash_password("password123")
        assert hashed != "password123"
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self, auth_service):
        hashed = auth_service._hash_password("password123")
        assert auth_service._verify_password("password123", hashed) is True

    def test_verify_password_incorrect(self, auth_service):
        hashed = auth_service._hash_password("password123")
        assert auth_service._verify_password("wrongpassword", hashed) is False


class TestSignup:
    @pytest.mark.asyncio
    async def test_signup_success(self, auth_service):
        auth_service.user_repo.get_by_email.return_value = None
        auth_service.user_repo.create.return_value = User(
            id=1,
            email="test@knou.ac.kr",
            password_hash="hashed",
            is_verified=False,
        )

        with patch.object(auth_service, "_send_verification_email", new_callable=AsyncMock):
            user = await auth_service.signup("test@knou.ac.kr", "password123")

        assert user.email == "test@knou.ac.kr"
        auth_service.user_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_signup_invalid_domain(self, auth_service):
        with pytest.raises(InvalidEmailDomainError):
            await auth_service.signup("test@gmail.com", "password123")

    @pytest.mark.asyncio
    async def test_signup_email_exists(self, auth_service):
        auth_service.user_repo.get_by_email.return_value = User(
            id=1, email="test@knou.ac.kr", password_hash="x", is_verified=True
        )

        with pytest.raises(EmailAlreadyExistsError):
            await auth_service.signup("test@knou.ac.kr", "password123")


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, auth_service):
        password_hash = auth_service._hash_password("password123")
        auth_service.user_repo.get_by_email.return_value = User(
            id=1,
            email="test@knou.ac.kr",
            password_hash=password_hash,
            is_verified=True,
        )

        user = await auth_service.login("test@knou.ac.kr", "password123")
        assert user.email == "test@knou.ac.kr"

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, auth_service):
        auth_service.user_repo.get_by_email.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await auth_service.login("unknown@knou.ac.kr", "password123")

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, auth_service):
        password_hash = auth_service._hash_password("password123")
        auth_service.user_repo.get_by_email.return_value = User(
            id=1,
            email="test@knou.ac.kr",
            password_hash=password_hash,
            is_verified=True,
        )

        with pytest.raises(InvalidCredentialsError):
            await auth_service.login("test@knou.ac.kr", "wrongpassword")

    @pytest.mark.asyncio
    async def test_login_email_not_verified(self, auth_service):
        password_hash = auth_service._hash_password("password123")
        auth_service.user_repo.get_by_email.return_value = User(
            id=1,
            email="test@knou.ac.kr",
            password_hash=password_hash,
            is_verified=False,
        )

        with pytest.raises(EmailNotVerifiedError):
            await auth_service.login("test@knou.ac.kr", "password123")
