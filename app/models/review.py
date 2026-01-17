from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, SmallInteger, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.tag import Tag
    from app.models.user import User


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    rating_overall: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1-5
    difficulty: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1-5
    workload: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1-5
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)

    course: Mapped["Course"] = relationship(back_populates="reviews")
    user: Mapped["User"] = relationship(back_populates="reviews")
    tags: Mapped[list["ReviewTag"]] = relationship(back_populates="review")

    def __repr__(self) -> str:
        return f"Review(id={self.id}, course_id={self.course_id}, rating={self.rating_overall})"


class ReviewTag(Base):
    __tablename__ = "review_tags"

    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)

    review: Mapped["Review"] = relationship(back_populates="tags")
    tag: Mapped["Tag"] = relationship()
