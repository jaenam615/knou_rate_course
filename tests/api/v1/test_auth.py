"""Unit tests for auth API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.models import User
from app.services.auth.errors import (
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidEmailDomainError,
)
from main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestSignup:
    @pytest.mark.asyncio
    async def test_signup_success(self, client):
        with patch("app.api.v1.auth.AuthService") as MockService:
            mock_service = MockService.return_value
            mock_service.signup = AsyncMock(
                return_value=User(
                    id=1, email="test@knou.ac.kr", password_hash="x", is_verified=False
                )
            )

            response = await client.post(
                "/api/v1/auth/signup",
                json={"email": "test@knou.ac.kr", "password": "password123"},
            )

        assert response.status_code == 201
        assert "message" in response.json()

    @pytest.mark.asyncio
    async def test_signup_invalid_domain(self, client):
        with patch("app.api.v1.auth.AuthService") as MockService:
            mock_service = MockService.return_value
            mock_service.signup = AsyncMock(
                side_effect=InvalidEmailDomainError("Must be KNOU email")
            )

            response = await client.post(
                "/api/v1/auth/signup",
                json={"email": "test@gmail.com", "password": "password123"},
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, client):
        with patch("app.api.v1.auth.AuthService") as MockService:
            mock_service = MockService.return_value
            mock_service.signup = AsyncMock(
                side_effect=EmailAlreadyExistsError("Email exists")
            )

            response = await client.post(
                "/api/v1/auth/signup",
                json={"email": "existing@knou.ac.kr", "password": "password123"},
            )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_signup_invalid_email_format(self, client):
        response = await client.post(
            "/api/v1/auth/signup",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_password_too_short(self, client):
        response = await client.post(
            "/api/v1/auth/signup",
            json={"email": "test@knou.ac.kr", "password": "short"},
        )
        assert response.status_code == 422


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client):
        with patch("app.api.v1.auth.AuthService") as MockService:
            mock_service = MockService.return_value
            mock_service.login = AsyncMock(
                return_value=User(
                    id=1, email="test@knou.ac.kr", password_hash="x", is_verified=True
                )
            )

            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "test@knou.ac.kr", "password": "password123"},
            )

        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        with patch("app.api.v1.auth.AuthService") as MockService:
            mock_service = MockService.return_value
            mock_service.login = AsyncMock(
                side_effect=InvalidCredentialsError("Invalid credentials")
            )

            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "test@knou.ac.kr", "password": "wrongpassword"},
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_email_not_verified(self, client):
        with patch("app.api.v1.auth.AuthService") as MockService:
            mock_service = MockService.return_value
            mock_service.login = AsyncMock(
                side_effect=EmailNotVerifiedError("Not verified")
            )

            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "test@knou.ac.kr", "password": "password123"},
            )

        assert response.status_code == 403
