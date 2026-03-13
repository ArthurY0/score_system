"""Services for Semester, Grade, Class, Course, Student, TeacherCourseClass."""
import io
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import openpyxl

from app.models.semester import Semester
from app.models.grade import Grade
from app.models.class_ import Class
from app.models.course import Course
from app.models.student import Student, Gender
from app.models.teacher_course_class import TeacherCourseClass
from app.schemas.base_data import (
    SemesterCreate, SemesterUpdate,
    GradeCreate, GradeUpdate,
    ClassCreate, ClassUpdate,
    CourseCreate, CourseUpdate,
    StudentCreate, StudentUpdate,
    AssignmentCreate,
    StudentImportResult,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _paginate(query, page: int, page_size: int):
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


# ── Semester ──────────────────────────────────────────────────────────────────

def list_semesters(db: Session, page=1, page_size=50):
    return _paginate(db.query(Semester).order_by(Semester.start_date.desc()), page, page_size)

def get_semester(db: Session, semester_id: int) -> Semester | None:
    return db.get(Semester, semester_id)

def get_semester_by_name(db: Session, name: str) -> Semester | None:
    return db.query(Semester).filter(Semester.name == name).first()

def create_semester(db: Session, data: SemesterCreate) -> Semester:
    s = Semester(**data.model_dump())
    db.add(s); db.commit(); db.refresh(s)
    return s

def update_semester(db: Session, s: Semester, data: SemesterUpdate) -> Semester:
    for k, v in data.model_dump().items():
        setattr(s, k, v)
    db.commit(); db.refresh(s)
    return s

def delete_semester(db: Session, s: Semester) -> None:
    db.delete(s); db.commit()


# ── Grade ─────────────────────────────────────────────────────────────────────

def list_grades(db: Session, page=1, page_size=50):
    return _paginate(db.query(Grade).order_by(Grade.name), page, page_size)

def get_grade(db: Session, grade_id: int) -> Grade | None:
    return db.get(Grade, grade_id)

def get_grade_by_name(db: Session, name: str) -> Grade | None:
    return db.query(Grade).filter(Grade.name == name).first()

def create_grade(db: Session, data: GradeCreate) -> Grade:
    g = Grade(name=data.name)
    db.add(g); db.commit(); db.refresh(g)
    return g

def update_grade(db: Session, g: Grade, data: GradeUpdate) -> Grade:
    g.name = data.name
    db.commit(); db.refresh(g)
    return g

def delete_grade(db: Session, g: Grade) -> None:
    db.delete(g); db.commit()


# ── Class ─────────────────────────────────────────────────────────────────────

def list_classes(db: Session, grade_id: int | None = None, page=1, page_size=50):
    q = db.query(Class)
    if grade_id:
        q = q.filter(Class.grade_id == grade_id)
    return _paginate(q.order_by(Class.name), page, page_size)

def get_class(db: Session, class_id: int) -> Class | None:
    return db.get(Class, class_id)

def create_class(db: Session, data: ClassCreate) -> Class:
    c = Class(name=data.name, grade_id=data.grade_id)
    db.add(c); db.commit(); db.refresh(c)
    return c

def update_class(db: Session, c: Class, data: ClassUpdate) -> Class:
    c.name = data.name; c.grade_id = data.grade_id
    db.commit(); db.refresh(c)
    return c

def delete_class(db: Session, c: Class) -> None:
    db.delete(c); db.commit()


# ── Course ────────────────────────────────────────────────────────────────────

def list_courses(db: Session, page=1, page_size=50):
    return _paginate(db.query(Course).order_by(Course.name), page, page_size)

def get_course(db: Session, course_id: int) -> Course | None:
    return db.get(Course, course_id)

def get_course_by_name(db: Session, name: str) -> Course | None:
    return db.query(Course).filter(Course.name == name).first()

def create_course(db: Session, data: CourseCreate) -> Course:
    c = Course(name=data.name)
    db.add(c); db.commit(); db.refresh(c)
    return c

def update_course(db: Session, c: Course, data: CourseUpdate) -> Course:
    c.name = data.name
    db.commit(); db.refresh(c)
    return c

def delete_course(db: Session, c: Course) -> None:
    db.delete(c); db.commit()


# ── Student ───────────────────────────────────────────────────────────────────

def list_students(db: Session, class_id: int | None = None, grade_id: int | None = None, page=1, page_size=50):
    q = db.query(Student)
    if class_id:
        q = q.filter(Student.class_id == class_id)
    elif grade_id:
        q = q.join(Class).filter(Class.grade_id == grade_id)
    return _paginate(q.order_by(Student.student_no), page, page_size)

def get_student(db: Session, student_id: int) -> Student | None:
    return db.get(Student, student_id)

def get_student_by_no(db: Session, student_no: str) -> Student | None:
    return db.query(Student).filter(Student.student_no == student_no).first()

def create_student(db: Session, data: StudentCreate) -> Student:
    s = Student(**data.model_dump())
    db.add(s); db.commit(); db.refresh(s)
    return s

def update_student(db: Session, s: Student, data: StudentUpdate) -> Student:
    for k, v in data.model_dump().items():
        setattr(s, k, v)
    db.commit(); db.refresh(s)
    return s

def delete_student(db: Session, s: Student) -> None:
    db.delete(s); db.commit()


_GENDER_MAP = {"男": Gender.MALE, "female": Gender.FEMALE, "male": Gender.MALE, "女": Gender.FEMALE}

def import_students_from_excel(db: Session, file_bytes: bytes) -> StudentImportResult:
    """Parse xlsx, columns: 学号, 姓名, 性别, 班级ID. Returns created count and error list."""
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes))
    ws = wb.active
    created = 0
    errors: list[str] = []

    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not any(row):
            continue
        try:
            student_no, name, gender_raw, class_id = str(row[0]).strip(), str(row[1]).strip(), str(row[2]).strip(), int(row[3])
        except (TypeError, ValueError) as e:
            errors.append(f"第{row_idx}行格式错误: {e}")
            continue

        if get_student_by_no(db, student_no):
            errors.append(f"第{row_idx}行学号 {student_no} 已存在，已跳过")
            continue

        if not db.get(Class, class_id):
            errors.append(f"第{row_idx}行班级ID {class_id} 不存在，已跳过")
            continue

        gender = _GENDER_MAP.get(gender_raw.lower(), Gender.MALE)
        s = Student(student_no=student_no, name=name, gender=gender, class_id=class_id)
        db.add(s)
        created += 1

    db.commit()
    return StudentImportResult(created=created, errors=errors)


# ── TeacherCourseClass ────────────────────────────────────────────────────────

def list_assignments(db: Session, teacher_id: int | None = None, semester_id: int | None = None, page=1, page_size=50):
    q = db.query(TeacherCourseClass)
    if teacher_id:
        q = q.filter(TeacherCourseClass.teacher_id == teacher_id)
    if semester_id:
        q = q.filter(TeacherCourseClass.semester_id == semester_id)
    return _paginate(q, page, page_size)

def get_assignment(db: Session, assignment_id: int) -> TeacherCourseClass | None:
    return db.get(TeacherCourseClass, assignment_id)

def assignment_exists(db: Session, data: AssignmentCreate) -> bool:
    return db.query(TeacherCourseClass).filter_by(
        teacher_id=data.teacher_id,
        course_id=data.course_id,
        class_id=data.class_id,
        semester_id=data.semester_id,
    ).first() is not None

def create_assignment(db: Session, data: AssignmentCreate) -> TeacherCourseClass:
    a = TeacherCourseClass(**data.model_dump())
    db.add(a); db.commit(); db.refresh(a)
    return a

def delete_assignment(db: Session, a: TeacherCourseClass) -> None:
    db.delete(a); db.commit()
