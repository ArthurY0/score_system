"""Phase 5.3/5.4: Report generation endpoints — PDF transcripts + Excel exports."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin_or_teacher
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.reports import BatchTranscriptRequest
from app.services import report_service as svc

router = APIRouter(prefix="/reports", tags=["reports"])


# ── 5.3 PDF Transcripts ─────────────────────────────────────────────────────

@router.get("/transcript/pdf")
def transcript_pdf(
    student_id: int = Query(...),
    semester_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Students can only download their own transcript
    if current_user.role == UserRole.STUDENT:
        linked = db.query(Student).filter_by(user_id=current_user.id).first()
        if not linked or linked.id != student_id:
            raise HTTPException(status_code=403, detail="只能下载自己的成绩单")

    pdf_bytes = svc.generate_transcript_pdf(db, student_id, semester_id)
    if pdf_bytes is None:
        raise HTTPException(status_code=404, detail="未找到该学生的成绩数据")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=transcript_{student_id}.pdf"},
    )


@router.post("/transcript/pdf/batch")
def batch_transcript_pdf(
    data: BatchTranscriptRequest,
    _: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    pdf_bytes = svc.generate_batch_transcript_pdf(db, data.class_id, data.semester_id)
    if pdf_bytes is None:
        raise HTTPException(status_code=404, detail="无成绩数据可生成")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=batch_transcript_{data.class_id}.pdf"},
    )


# ── 5.4 Excel Exports ───────────────────────────────────────────────────────

@router.get("/class-summary/excel")
def class_summary_excel(
    class_id: int = Query(...),
    semester_id: int = Query(...),
    _: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    excel_bytes = svc.generate_class_summary_excel(db, class_id, semester_id)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=class_summary_{class_id}.xlsx"},
    )


@router.get("/grade-ranking/excel")
def grade_ranking_excel(
    grade_id: int = Query(...),
    semester_id: int = Query(...),
    _: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    excel_bytes = svc.generate_grade_ranking_excel(db, grade_id, semester_id)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=grade_ranking_{grade_id}.xlsx"},
    )


@router.get("/student-scores/excel")
def student_scores_excel(
    student_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Students can only download their own scores
    if current_user.role == UserRole.STUDENT:
        linked = db.query(Student).filter_by(user_id=current_user.id).first()
        if not linked or linked.id != student_id:
            raise HTTPException(status_code=403, detail="只能下载自己的成绩")

    excel_bytes = svc.generate_student_scores_excel(db, student_id)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=student_scores_{student_id}.xlsx"},
    )
