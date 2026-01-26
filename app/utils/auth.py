from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models import User
from app.repositories import UserRepository

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
    }
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return int(payload.get("sub"))
    except jwt.PyJWTError:
        return None


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    token = credentials.credentials
    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_optional_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(optional_security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """Get current user if authenticated, otherwise return None."""
    if credentials is None:
        return None

    token = credentials.credentials
    user_id = decode_access_token(token)

    if user_id is None:
        return None

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user is None or not user.is_verified:
        return None

    return user


OptionalCurrentUser = Annotated[User | None, Depends(get_optional_current_user)]


class InsufficientReviewsError(Exception):
    """Raised when user doesn't have enough reviews for full access."""

    pass


async def get_current_user_with_full_access(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get current user and verify they have full access (3+ reviews)."""
    user = await get_current_user(credentials, db)
    if not user.has_full_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Write {3 - user.review_count} more review(s) to unlock full access",
        )
    return user


CurrentUserWithFullAccess = Annotated[User, Depends(get_current_user_with_full_access)]
