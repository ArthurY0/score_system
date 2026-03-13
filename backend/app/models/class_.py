from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Class(Base):
    __tablename__ = "classes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    grade_id: Mapped[int] = mapped_column(Integer, ForeignKey("grades.id"), nullable=False)
    grade: Mapped["Grade"] = relationship("Grade", back_populates="classes")  # noqa: F821
    students: Mapped[list["Student"]] = relationship("Student", back_populates="class_", lazy="select")  # noqa: F821
