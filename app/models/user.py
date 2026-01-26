from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.auth import AuthConstants
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.review import Review


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_verification_token", "verification_token"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verification_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    reviews: Mapped[list["Review"]] = relationship(back_populates="user")

    @property
    def has_full_access(self) -> bool:
        return self.review_count >= AuthConstants.REQUIRED_REVIEWS_FOR_FULL_ACCESS

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email})"
