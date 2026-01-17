from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Major(Base):
    __tablename__ = "majors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    courses: Mapped[list["Course"]] = relationship(back_populates="major")

    def __repr__(self) -> str:
        return f"Major(id={self.id}, name={self.name})"


from app.models.course import Course
