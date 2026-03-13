"""Score management service — entry, update, batch, Excel import, audit logs."""
import io
from decimal import Decimal, InvalidOperation

import openpyxl
from sqlalchemy.orm import Session

from app.models.score import Score, ScoreAuditLog
from app.models.student import Student
from app.models.teacher_course_class import TeacherCourseClass
from app.schemas.score import BatchScoreCreate, BatchScoreResult, ScoreCreate, ScoreImportResult, ScoreUpdate


# ── Permission helpers ────────────────────────────────────────────────────────

def teacher_is_assigned(db: Session, teacher_id: int, course_id: int, class_id: int, semester_id: int) -> bool:
    return db.query(TeacherCourseClass).filter_by(
        teacher_id=teacher_id, course_id=course_id, class_id=class_id, semester_id=semester_id
    ).first() is not None


# ── Query helpers ─────────────────────────────────────────────────────────────

def get_score(db: Session, score_id: int) -> Score | None:
    return db.get(Score, score_id)


def get_score_by_unique(db: Session, student_id: int, course_id: int, semester_id: int) -> Score | None:
    return db.query(Score).filter_by(
        student_id=student_id, course_id=course_id, semester_id=semester_id
    ).first()


def list_scores(
    db: Session,
    student_id: int | None = None,
    class_id: int | None = None,
    course_id: int | None = None,
    semester_id: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Score], int]:
    q = db.query(Score)
    if student_id:
        q = q.filter(Score.student_id == student_id)
    if class_id:
        q = q.filter(Score.class_id == class_id)
    if course_id:
        q = q.filter(Score.course_id == course_id)
    if semester_id:
        q = q.filter(Score.semester_id == semester_id)
    total = q.count()
    return q.offset((page - 1) * page_size).limit(page_size).all(), total


def list_student_scores(db: Session, student_id: int, semester_id: int | None = None, page: int = 1, page_size: int = 50):
    q = db.query(Score).filter(Score.student_id == student_id)
    if semester_id:
        q = q.filter(Score.semester_id == semester_id)
    total = q.count()
    return q.offset((page - 1) * page_size).limit(page_size).all(), total


# ── Write helpers ─────────────────────────────────────────────────────────────

def _create_audit_log(db: Session, score: Score, old_score: Decimal | None, action: str, changed_by: int, reason: str | None = None):
    log = ScoreAuditLog(
        score_id=score.id,
        old_score=old_score,
        new_score=score.score,
        changed_by=changed_by,
        action=action,
        reason=reason,
    )
    db.add(log)


def create_score(db: Session, data: ScoreCreate, teacher_id: int) -> Score:
    s = Score(
        student_id=data.student_id,
        course_id=data.course_id,
        class_id=data.class_id,
        semester_id=data.semester_id,
        teacher_id=teacher_id,
        score=data.score,
    )
    db.add(s)
    db.flush()  # get id before audit log
    _create_audit_log(db, s, old_score=None, action="created", changed_by=teacher_id)
    db.commit()
    db.refresh(s)
    return s


def update_score(db: Session, score: Score, data: ScoreUpdate, changed_by: int) -> Score:
    old = score.score
    score.score = data.score
    db.flush()
    _create_audit_log(db, score, old_score=old, action="updated", changed_by=changed_by, reason=data.reason)
    db.commit()
    db.refresh(score)
    return score


def delete_score(db: Session, score: Score) -> None:
    db.delete(score)
    db.commit()


# ── Batch entry ───────────────────────────────────────────────────────────────

def batch_upsert_scores(db: Session, data: BatchScoreCreate, teacher_id: int) -> BatchScoreResult:
    created = updated = 0
    errors: list[str] = []

    for entry in data.entries:
        existing = get_score_by_unique(db, entry.student_id, data.course_id, data.semester_id)
        if existing:
            old = existing.score
            existing.score = entry.score
            db.flush()
            _create_audit_log(db, existing, old_score=old, action="updated", changed_by=teacher_id, reason="批量录入更新")
            updated += 1
        else:
            s = Score(
                student_id=entry.student_id, course_id=data.course_id,
                class_id=data.class_id, semester_id=data.semester_id,
                teacher_id=teacher_id, score=entry.score,
            )
            db.add(s)
            db.flush()
            _create_audit_log(db, s, old_score=None, action="created", changed_by=teacher_id)
            created += 1

    db.commit()
    return BatchScoreResult(created=created, updated=updated, errors=errors)


# ── Excel import ──────────────────────────────────────────────────────────────

def import_scores_from_excel(
    db: Session,
    file_bytes: bytes,
    class_id: int,
    course_id: int,
    semester_id: int,
    teacher_id: int,
) -> ScoreImportResult:
    """
    Expected columns: 学号, 分数
    Upserts scores and creates audit logs.
    """
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes))
    ws = wb.active
    created = updated = 0
    errors: list[str] = []

    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not any(row):
            continue
        try:
            student_no = str(row[0]).strip()
            score_val = Decimal(str(row[1]))
            if score_val < 0 or score_val > 150:
                raise ValueError(f"分数 {score_val} 超出范围 (0-150)")
        except (InvalidOperation, ValueError, TypeError) as e:
            errors.append(f"第{row_idx}行格式错误: {e}")
            continue

        student = db.query(Student).filter_by(student_no=student_no).first()
        if not student:
            errors.append(f"第{row_idx}行学号 {student_no} 不存在，已跳过")
            continue

        existing = get_score_by_unique(db, student.id, course_id, semester_id)
        if existing:
            old = existing.score
            existing.score = score_val
            db.flush()
            _create_audit_log(db, existing, old_score=old, action="updated", changed_by=teacher_id, reason="Excel导入更新")
            updated += 1
        else:
            s = Score(
                student_id=student.id, course_id=course_id, class_id=class_id,
                semester_id=semester_id, teacher_id=teacher_id, score=score_val,
            )
            db.add(s)
            db.flush()
            _create_audit_log(db, s, old_score=None, action="created", changed_by=teacher_id, reason="Excel导入")
            created += 1

    db.commit()
    return ScoreImportResult(created=created, updated=updated, errors=errors)


# ── Audit logs ────────────────────────────────────────────────────────────────

def list_audit_logs(db: Session, score_id: int) -> list[ScoreAuditLog]:
    return db.query(ScoreAuditLog).filter_by(score_id=score_id).order_by(ScoreAuditLog.changed_at).all()
