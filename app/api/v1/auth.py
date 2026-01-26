from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import RATE_LIMIT_AUTH, limiter
from app.db import get_db
from app.schemas import (
    LoginRequest,
    MessageResponse,
    ResendVerificationRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth.auth import AuthService
from app.services.auth.errors import (
    AccountDeletedError,
    AuthServiceError,
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidEmailDomainError,
    InvalidVerificationTokenError,
    VerificationTokenExpiredError,
)
from app.utils import CurrentUser, create_access_token

router = APIRouter()

"""
Authentication and User Management Endpoints
"""


@router.post("/signup", response_model=MessageResponse, status_code=201)
@limiter.limit(RATE_LIMIT_AUTH)
async def signup(
    request: Request,
    data: SignupRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    auth_service = AuthService(db)

    try:
        await auth_service.signup(str(data.email), data.password)
    except InvalidEmailDomainError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AccountDeletedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return MessageResponse(
        message="Signup successful. Please check your email to verify your account."
    )


@router.post("/verify-email", response_model=MessageResponse)
@limiter.limit(RATE_LIMIT_AUTH)
async def verify_email(
    request: Request,
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    auth_service = AuthService(db)

    try:
        await auth_service.verify_email(data.token)
    except InvalidVerificationTokenError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except VerificationTokenExpiredError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return MessageResponse(message="Email verified successfully. You can now login.")


@router.post("/login", response_model=TokenResponse)
@limiter.limit(RATE_LIMIT_AUTH)
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    auth_service = AuthService(db)

    try:
        user = await auth_service.login(str(data.email), data.password)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except AccountDeletedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except EmailNotVerifiedError as e:
        raise HTTPException(status_code=403, detail=str(e))

    access_token = create_access_token(user.id)
    return TokenResponse(access_token=access_token)


@router.post("/resend-verification", response_model=MessageResponse)
@limiter.limit(RATE_LIMIT_AUTH)
async def resend_verification(
    request: Request,
    data: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    auth_service = AuthService(db)

    try:
        await auth_service.resend_verification(str(data.email))
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AuthServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # TODO: Send verification email with token

    return MessageResponse(message="Verification email sent.")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.delete("/me", response_model=MessageResponse)
async def delete_account(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Delete the current user's account (soft delete)."""
    auth_service = AuthService(db)
    await auth_service.delete_account(current_user)
    return MessageResponse(message="Account deleted successfully.")
