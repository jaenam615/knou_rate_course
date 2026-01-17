import enum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TagType(enum.Enum):
    EVAL_METHOD = "EVAL_METHOD"  # Fixed tags like 기말시험, 기말과제물
    FREEFORM = "FREEFORM"  # Free tags like 기출많음, 오픈북


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    type: Mapped[TagType] = mapped_column(Enum(TagType), nullable=False)

    def __repr__(self) -> str:
        return f"Tag(id={self.id}, name={self.name}, type={self.type})"
