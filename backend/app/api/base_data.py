"""
Phase 3 API routes: Semesters, Grades, Classes, Courses, Students, Assignments.
All write operations require admin role; read operations allow admin+teacher.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin, require_admin_or_teacher
from app.models.user import User
from app.schemas.base_data import (
    SemesterCreate, SemesterUpdate, SemesterResponse,
    GradeCreate, GradeUpdate, GradeResponse,
    ClassCreate, ClassUpdate, ClassResponse,
    CourseCreate, CourseUpdate, CourseResponse,
    StudentCreate, StudentUpdate, StudentResponse, StudentImportResult,
    AssignmentCreate, AssignmentResponse,
    ListResponse,
)
from app.services import base_data_service as svc


# ═══════════════════════════════════════════════════════════
# SEMESTERS
# ═══════════════════════════════════════════════════════════
semesters_router = APIRouter(prefix="/semesters", tags=["semesters"])


@semesters_router.get("", response_model=ListResponse)
def list_semesters(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
                   _: User = Depends(require_admin_or_teacher), db: Session = Depends(get_db)):
    items, total = svc.list_semesters(db, page, page_size)
    return {"items": [SemesterResponse.model_validate(s) for s in items], "total": total, "page": page, "page_size": page_size}


@semesters_router.post("", response_model=SemesterResponse, status_code=201)
def create_semester(data: SemesterCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    if svc.get_semester_by_name(db, data.name):
        raise HTTPException(status_code=409, detail="学期名称已存在")
    return svc.create_semester(db, data)


@semesters_router.get("/{semester_id}", response_model=SemesterResponse)
def get_semester(semester_id: int, _: User = Depends(require_admin_or_teacher), db: Session = Depends(get_db)):
    s = svc.get_semester(db, semester_id)
    if not s:
        raise HTTPException(status_code=404, detail="学期不存在")
    return s


@semesters_router.put("/{semester_id}", response_model=SemesterResponse)
def update_semester(semester_id: int, data: SemesterUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    s = svc.get_semester(db, semester_id)
    if not s:
        raise HTTPException(status_code=404, detail="学期不存在")
    return svc.update_semester(db, s, data)


@semesters_router.delete("/{semester_id}", status_code=204)
def delete_semester(semester_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    s = svc.get_semester(db, semester_id)
    if not s:
        raise HTTPException(status_code=404, detail="学期不存在")
    svc.delete_semester(db, s)


# ═══════════════════════════════════════════════════════════
# GRADES
# ═══════════════════════════════════════════════════════════
grades_router = APIRouter(prefix="/grades", tags=["grades"])


@grades_router.get("", response_model=ListResponse)
def list_grades(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
                _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items, total = svc.list_grades(db, page, page_size)
    return {"items": [GradeResponse.model_validate(g) for g in items], "total": total, "page": page, "page_size": page_size}


@grades_router.post("", response_model=GradeResponse, status_code=201)
def create_grade(data: GradeCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    if svc.get_grade_by_name(db, data.name):
        raise HTTPException(status_code=409, detail="年级名称已存在")
    return svc.create_grade(db, data)


@grades_router.get("/{grade_id}", response_model=GradeResponse)
def get_grade(grade_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    g = svc.get_grade(db, grade_id)
    if not g:
        raise HTTPException(status_code=404, detail="年级不存在")
    return g


@grades_router.put("/{grade_id}", response_model=GradeResponse)
def update_grade(grade_id: int, data: GradeUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    g = svc.get_grade(db, grade_id)
    if not g:
        raise HTTPException(status_code=404, detail="年级不存在")
    return svc.update_grade(db, g, data)


@grades_router.delete("/{grade_id}", status_code=204)
def delete_grade(grade_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    g = svc.get_grade(db, grade_id)
    if not g:
        raise HTTPException(status_code=404, detail="年级不存在")
    svc.delete_grade(db, g)


# ═══════════════════════════════════════════════════════════
# CLASSES
# ═══════════════════════════════════════════════════════════
classes_router = APIRouter(prefix="/classes", tags=["classes"])


@classes_router.get("", response_model=ListResponse)
def list_classes(grade_id: int | None = Query(None), page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
                 _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items, total = svc.list_classes(db, grade_id=grade_id, page=page, page_size=page_size)
    return {"items": [ClassResponse.model_validate(c) for c in items], "total": total, "page": page, "page_size": page_size}


@classes_router.post("", response_model=ClassResponse, status_code=201)
def create_class(data: ClassCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    if not svc.get_grade(db, data.grade_id):
        raise HTTPException(status_code=404, detail="年级不存在")
    return svc.create_class(db, data)


@classes_router.get("/{class_id}", response_model=ClassResponse)
def get_class(class_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = svc.get_class(db, class_id)
    if not c:
        raise HTTPException(status_code=404, detail="班级不存在")
    return c


@classes_router.put("/{class_id}", response_model=ClassResponse)
def update_class(class_id: int, data: ClassUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    c = svc.get_class(db, class_id)
    if not c:
        raise HTTPException(status_code=404, detail="班级不存在")
    if not svc.get_grade(db, data.grade_id):
        raise HTTPException(status_code=404, detail="年级不存在")
    return svc.update_class(db, c, data)


@classes_router.delete("/{class_id}", status_code=204)
def delete_class(class_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    c = svc.get_class(db, class_id)
    if not c:
        raise HTTPException(status_code=404, detail="班级不存在")
    svc.delete_class(db, c)


# ═══════════════════════════════════════════════════════════
# COURSES
# ═══════════════════════════════════════════════════════════
courses_router = APIRouter(prefix="/courses", tags=["courses"])


@courses_router.get("", response_model=ListResponse)
def list_courses(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
                 _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items, total = svc.list_courses(db, page, page_size)
    return {"items": [CourseResponse.model_validate(c) for c in items], "total": total, "page": page, "page_size": page_size}


@courses_router.post("", response_model=CourseResponse, status_code=201)
def create_course(data: CourseCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    if svc.get_course_by_name(db, data.name):
        raise HTTPException(status_code=409, detail="课程名称已存在")
    return svc.create_course(db, data)


@courses_router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = svc.get_course(db, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="课程不存在")
    return c


@courses_router.put("/{course_id}", response_model=CourseResponse)
def update_course(course_id: int, data: CourseUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    c = svc.get_course(db, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="课程不存在")
    return svc.update_course(db, c, data)


@courses_router.delete("/{course_id}", status_code=204)
def delete_course(course_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    c = svc.get_course(db, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="课程不存在")
    svc.delete_course(db, c)


# ═══════════════════════════════════════════════════════════
# STUDENTS
# ═══════════════════════════════════════════════════════════
students_router = APIRouter(prefix="/students", tags=["students"])


@students_router.get("", response_model=ListResponse)
def list_students(
    class_id: int | None = Query(None),
    grade_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    items, total = svc.list_students(db, class_id=class_id, grade_id=grade_id, page=page, page_size=page_size)
    return {"items": [StudentResponse.model_validate(s) for s in items], "total": total, "page": page, "page_size": page_size}


@students_router.post("", response_model=StudentResponse, status_code=201)
def create_student(data: StudentCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    if not svc.get_class(db, data.class_id):
        raise HTTPException(status_code=404, detail="班级不存在")
    if svc.get_student_by_no(db, data.student_no):
        raise HTTPException(status_code=409, detail="学号已存在")
    return svc.create_student(db, data)


@students_router.post("/import", response_model=StudentImportResult)
async def import_students(
    file: UploadFile = File(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    content = await file.read()
    return svc.import_students_from_excel(db, content)


@students_router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, _: User = Depends(require_admin_or_teacher), db: Session = Depends(get_db)):
    s = svc.get_student(db, student_id)
    if not s:
        raise HTTPException(status_code=404, detail="学生不存在")
    return s


@students_router.put("/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, data: StudentUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    s = svc.get_student(db, student_id)
    if not s:
        raise HTTPException(status_code=404, detail="学生不存在")
    if data.class_id != s.class_id and not svc.get_class(db, data.class_id):
        raise HTTPException(status_code=404, detail="班级不存在")
    return svc.update_student(db, s, data)


@students_router.delete("/{student_id}", status_code=204)
def delete_student(student_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    s = svc.get_student(db, student_id)
    if not s:
        raise HTTPException(status_code=404, detail="学生不存在")
    svc.delete_student(db, s)


# ═══════════════════════════════════════════════════════════
# TEACHER-COURSE-CLASS ASSIGNMENTS
# ═══════════════════════════════════════════════════════════
assignments_router = APIRouter(prefix="/assignments", tags=["assignments"])


@assignments_router.get("", response_model=ListResponse)
def list_assignments(
    teacher_id: int | None = Query(None),
    semester_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.user import UserRole
    # Teachers can only see their own assignments
    effective_teacher_id = teacher_id
    if current_user.role == UserRole.TEACHER:
        effective_teacher_id = current_user.id
    items, total = svc.list_assignments(db, teacher_id=effective_teacher_id, semester_id=semester_id, page=page, page_size=page_size)
    return {"items": [AssignmentResponse.model_validate(a) for a in items], "total": total, "page": page, "page_size": page_size}


@assignments_router.post("", response_model=AssignmentResponse, status_code=201)
def create_assignment(data: AssignmentCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    if svc.assignment_exists(db, data):
        raise HTTPException(status_code=409, detail="该分配关系已存在")
    return svc.create_assignment(db, data)


@assignments_router.delete("/{assignment_id}", status_code=204)
def delete_assignment(assignment_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    a = svc.get_assignment(db, assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="分配关系不存在")
    svc.delete_assignment(db, a)
