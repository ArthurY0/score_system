"""Phase 5.1: Statistics API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin_or_teacher
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.statistics import (
    ClassCourseStatistics,
    ClassRankingResponse,
    GradeComparisonResponse,
    GradeRankingResponse,
    ScoreTrendResponse,
    StudentStatisticsResponse,
)
from app.services import statistics_service as svc

router = APIRouter(prefix="/statistics", tags=["statistics"])


# ── 1. Class-course statistics ───────────────────────────────────────────────

@router.get("/class-course", response_model=ClassCourseStatistics)
def class_course_statistics(
    class_id: int = Query(...),
    course_id: int = Query(...),
    semester_id: int = Query(...),
    _: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    result = svc.class_course_statistics(db, class_id, course_id, semester_id)
    if result is None:
        raise HTTPException(status_code=404, detail="无成绩数据")
    return result


# ── 2. Class ranking ─────────────────────────────────────────────────────────

@router.get("/class-ranking", response_model=ClassRankingResponse)
def class_ranking(
    class_id: int = Query(...),
    course_id: int = Query(...),
    semester_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    items, total = svc.class_ranking(db, class_id, course_id, semester_id, page, page_size)
    return ClassRankingResponse(items=items, total=total, page=page, page_size=page_size)


# ── 3. Grade ranking ─────────────────────────────────────────────────────────

@router.get("/grade-ranking", response_model=GradeRankingResponse)
def grade_ranking(
    grade_id: int = Query(...),
    semester_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    items, total = svc.grade_ranking(db, grade_id, semester_id, page, page_size)
    return GradeRankingResponse(items=items, total=total, page=page, page_size=page_size)


# ── 4. Student personal statistics ──────────────────────────────────────────

@router.get("/student/{student_id}", response_model=StudentStatisticsResponse)
def student_statistics(
    student_id: int,
    semester_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Students can only view their own stats
    if current_user.role == UserRole.STUDENT:
        linked = db.query(Student).filter_by(user_id=current_user.id).first()
        if not linked or linked.id != student_id:
            raise HTTPException(status_code=403, detail="只能查看自己的统计信息")

    result = svc.student_statistics(db, student_id, semester_id)
    if result is None:
        raise HTTPException(status_code=404, detail="未找到该学生的成绩数据")
    return result


# ── 5. Score trend ───────────────────────────────────────────────────────────

@router.get("/trend", response_model=ScoreTrendResponse)
def score_trend(
    student_id: int = Query(...),
    course_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Students can only view their own trend
    if current_user.role == UserRole.STUDENT:
        linked = db.query(Student).filter_by(user_id=current_user.id).first()
        if not linked or linked.id != student_id:
            raise HTTPException(status_code=403, detail="只能查看自己的趋势")

    result = svc.score_trend(db, student_id, course_id)
    if result is None:
        raise HTTPException(status_code=404, detail="未找到成绩趋势数据")
    return result


# ── 6. Grade comparison ─────────────────────────────────────────────────────

@router.get("/comparison", response_model=GradeComparisonResponse)
def grade_comparison(
    grade_id: int = Query(...),
    course_id: int = Query(...),
    semester_id: int = Query(...),
    _: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    result = svc.grade_comparison(db, grade_id, course_id, semester_id)
    if result is None:
        raise HTTPException(status_code=404, detail="无对比数据")
    return result
