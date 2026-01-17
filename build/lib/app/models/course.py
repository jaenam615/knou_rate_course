from sqlalchemy import Boolean, ForeignKey, Integer, String, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    major_id: Mapped[int] = mapped_column(ForeignKey("majors.id"), nullable=False)
    course_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    credits: Mapped[int] = mapped_column(SmallInteger, default=3)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    major: Mapped["Major"] = relationship(back_populates="courses")
    offerings: Mapped[list["CourseOffering"]] = relationship(back_populates="course")
    reviews: Mapped[list["Review"]] = relationship(back_populates="course")

    def __repr__(self) -> str:
        return f"Course(id={self.id}, name={self.name})"


class CourseOffering(Base):
    __tablename__ = "course_offerings"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    semester: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1 or 2
    grade_target: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1-4
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)

    course: Mapped["Course"] = relationship(back_populates="offerings")

    def __repr__(self) -> str:
        return f"CourseOffering(course_id={self.course_id}, year={self.year}, semester={self.semester})"


from app.models.major import Major
from app.models.review import Review
