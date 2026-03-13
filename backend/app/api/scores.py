"""Phase 4: Score management API."""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin, require_admin_or_teacher
from app.models.user import User, UserRole
from app.models.student import Student
from app.schemas.score import (
    AuditLogResponse, BatchScoreCreate, BatchScoreResult,
    ScoreCreate, ScoreImportResult, ScoreListResponse, ScoreResponse, ScoreUpdate,
)
from app.services import score_service as svc

router = APIRouter(prefix="/scores", tags=["scores"])


def _get_score_or_404(db: Session, score_id: int):
    s = svc.get_score(db, score_id)
    if not s:
        raise HTTPException(status_code=404, detail="成绩不存在")
    return s


def _assert_teacher_can_write(db: Session, user: User, class_id: int, course_id: int, semester_id: int):
    """Raise 403 if teacher is not assigned to the course/class/semester."""
    if user.role == UserRole.ADMIN:
        return
    if not svc.teacher_is_assigned(db, user.id, course_id, class_id, semester_id):
        raise HTTPException(status_code=403, detail="您未被分配到该课程/班级，无法录入成绩")


# ── List / Query ──────────────────────────────────────────────────────────────

@router.get("", response_model=ScoreListResponse)
def list_scores(
    student_id: int | None = Query(None),
    class_id: int | None = Query(None),
    course_id: int | None = Query(None),
    semester_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="无权查看所有成绩")
    items, total = svc.list_scores(
        db, student_id=student_id, class_id=class_id,
        course_id=course_id, semester_id=semester_id,
        page=page, page_size=page_size,
    )
    return ScoreListResponse(
        items=[ScoreResponse.model_validate(s) for s in items],
        total=total, page=page, page_size=page_size,
    )


@router.get("/my", response_model=ScoreListResponse)
def my_scores(
    semester_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Student endpoint: returns only the logged-in student's own scores."""
    student = db.query(Student).filter_by(user_id=current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="未找到关联的学生档案")
    items, total = svc.list_student_scores(db, student.id, semester_id=semester_id, page=page, page_size=page_size)
    return ScoreListResponse(
        items=[ScoreResponse.model_validate(s) for s in items],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{score_id}", response_model=ScoreResponse)
def get_score(
    score_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="无权访问")
    return _get_score_or_404(db, score_id)


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("", response_model=ScoreResponse, status_code=201)
def create_score(
    data: ScoreCreate,
    current_user: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    _assert_teacher_can_write(db, current_user, data.class_id, data.course_id, data.semester_id)
    if svc.get_score_by_unique(db, data.student_id, data.course_id, data.semester_id):
        raise HTTPException(status_code=409, detail="该学生本学期此课程成绩已存在")
    return svc.create_score(db, data, teacher_id=current_user.id)


# ── Batch create / upsert ─────────────────────────────────────────────────────

@router.post("/batch", response_model=BatchScoreResult)
def batch_scores(
    data: BatchScoreCreate,
    current_user: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    _assert_teacher_can_write(db, current_user, data.class_id, data.course_id, data.semester_id)
    return svc.batch_upsert_scores(db, data, teacher_id=current_user.id)


# ── Excel import ──────────────────────────────────────────────────────────────

@router.post("/import", response_model=ScoreImportResult)
async def import_scores(
    class_id: int = Query(...),
    course_id: int = Query(...),
    semester_id: int = Query(...),
    teacher_id: int = Query(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    _assert_teacher_can_write(db, current_user, class_id, course_id, semester_id)
    content = await file.read()
    return svc.import_scores_from_excel(db, content, class_id, course_id, semester_id, teacher_id)


# ── Update ────────────────────────────────────────────────────────────────────

@router.put("/{score_id}", response_model=ScoreResponse)
def update_score(
    score_id: int,
    data: ScoreUpdate,
    current_user: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    score = _get_score_or_404(db, score_id)
    _assert_teacher_can_write(db, current_user, score.class_id, score.course_id, score.semester_id)
    return svc.update_score(db, score, data, changed_by=current_user.id)


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{score_id}", status_code=204)
def delete_score(
    score_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    score = _get_score_or_404(db, score_id)
    svc.delete_score(db, score)


# ── Audit logs ────────────────────────────────────────────────────────────────

@router.get("/{score_id}/audit-logs", response_model=list[AuditLogResponse])
def get_audit_logs(
    score_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="无权查看审计日志")
    _get_score_or_404(db, score_id)
    return [AuditLogResponse.model_validate(l) for l in svc.list_audit_logs(db, score_id)]
