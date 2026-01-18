from typing import TYPE_CHECKING

from sqlalchemy import Boolean
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.course import CourseStatus
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.major import Major
    from app.models.review import Review


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        Index("ix_courses_major_id", "major_id"),
        Index("ix_courses_is_archived", "is_archived"),
        Index("ix_courses_major_archived", "major_id", "is_archived"),
        Index("ix_courses_name", "name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    major_id: Mapped[int] = mapped_column(ForeignKey("majors.id"), nullable=False)
    course_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    major: Mapped["Major"] = relationship(back_populates="courses")
    offerings: Mapped[list["CourseOffering"]] = relationship(back_populates="course")
    reviews: Mapped[list["Review"]] = relationship(back_populates="course")

    def __repr__(self) -> str:
        return f"Course(id={self.id}, name={self.name})"


class CourseOffering(Base):
    __tablename__ = "course_offerings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    semester: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1 or 2
    grade_target: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1-4
    status: Mapped[CourseStatus] = mapped_column(
        SAEnum(CourseStatus, name="course_status"), default=CourseStatus.ACTIVE
    )

    course: Mapped["Course"] = relationship(back_populates="offerings")

    def __repr__(self) -> str:
        return f"CourseOffering(course_id={self.course_id}, semester={self.semester})"
