from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Score(Base):
    __tablename__ = "scores"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", "semester_id", name="uq_student_course_semester"),
        Index("ix_scores_sem_class_course", "semester_id", "class_id", "course_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    class_id: Mapped[int] = mapped_column(Integer, ForeignKey("classes.id"), nullable=False, index=True)
    semester_id: Mapped[int] = mapped_column(Integer, ForeignKey("semesters.id"), nullable=False, index=True)
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ScoreAuditLog(Base):
    __tablename__ = "score_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    score_id: Mapped[int] = mapped_column(Integer, ForeignKey("scores.id", ondelete="CASCADE"), nullable=False, index=True)
    old_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    new_score: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    changed_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # "created" | "updated"
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
