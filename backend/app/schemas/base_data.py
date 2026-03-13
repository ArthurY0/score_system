from datetime import date, datetime
from pydantic import BaseModel, Field
from app.models.student import Gender


# ── Semester ──────────────────────────────────────────────

class SemesterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    start_date: date
    end_date: date
    is_active: bool = False


class SemesterCreate(SemesterBase):
    pass


class SemesterUpdate(SemesterBase):
    pass


class SemesterResponse(SemesterBase):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Grade ─────────────────────────────────────────────────

class GradeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class GradeCreate(GradeBase):
    pass


class GradeUpdate(GradeBase):
    pass


class GradeResponse(GradeBase):
    id: int
    model_config = {"from_attributes": True}


# ── Class ─────────────────────────────────────────────────

class ClassBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    grade_id: int


class ClassCreate(ClassBase):
    pass


class ClassUpdate(ClassBase):
    pass


class ClassResponse(ClassBase):
    id: int
    model_config = {"from_attributes": True}


# ── Course ────────────────────────────────────────────────

class CourseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class CourseCreate(CourseBase):
    pass


class CourseUpdate(CourseBase):
    pass


class CourseResponse(CourseBase):
    id: int
    model_config = {"from_attributes": True}


# ── Student ───────────────────────────────────────────────

class StudentBase(BaseModel):
    student_no: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=50)
    gender: Gender
    class_id: int


class StudentCreate(StudentBase):
    pass


class StudentUpdate(StudentBase):
    pass


class StudentResponse(StudentBase):
    id: int
    user_id: int | None = None
    model_config = {"from_attributes": True}


class StudentImportResult(BaseModel):
    created: int
    errors: list[str]


# ── TeacherCourseClass ────────────────────────────────────

class AssignmentCreate(BaseModel):
    teacher_id: int
    course_id: int
    class_id: int
    semester_id: int


class AssignmentResponse(AssignmentCreate):
    id: int
    model_config = {"from_attributes": True}


# ── Generic list response ─────────────────────────────────

class ListResponse(BaseModel):
    items: list
    total: int
    page: int = 1
    page_size: int = 20
