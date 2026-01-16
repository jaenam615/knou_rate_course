from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils import create_access_token, CurrentUser
from app.db import get_db
from app.schemas import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
    VerifyEmailRequest,
    ResendVerificationRequest,
)
from app.services import AuthService
from app.services.auth import (
    InvalidEmailDomainError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    EmailNotVerifiedError,
    InvalidVerificationTokenError,
    VerificationTokenExpiredError,
    AuthServiceError,
)

router = APIRouter()


@router.post("/signup", response_model=MessageResponse, status_code=201)
async def signup(
    data: SignupRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    auth_service = AuthService(db)

    try:
        user, token = await auth_service.signup(data.email, data.password)
    except InvalidEmailDomainError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # TODO: Send verification email with token
    # For now, just return success message
    # In production: send_verification_email(user.email, token)

    return MessageResponse(
        message="Signup successful. Please check your email to verify your account."
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
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
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    auth_service = AuthService(db)

    try:
        user = await auth_service.login(data.email, data.password)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EmailNotVerifiedError as e:
        raise HTTPException(status_code=403, detail=str(e))

    access_token = create_access_token(user.id)
    return TokenResponse(access_token=access_token)


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    data: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    auth_service = AuthService(db)

    try:
        user, token = await auth_service.resend_verification(data.email)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AuthServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # TODO: Send verification email with token

    return MessageResponse(message="Verification email sent.")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)
