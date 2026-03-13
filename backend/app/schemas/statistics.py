"""Phase 5.1: Statistics response schemas."""
from pydantic import BaseModel


# ── Score distribution bucket ────────────────────────────────────────────────

class ScoreDistributionBucket(BaseModel):
    range: str  # e.g. "<30", "30-39", "40-59", "60-69", "70-84", "85-100", "100-150"
    count: int


# ── Class-course statistics ──────────────────────────────────────────────────

class ClassCourseStatistics(BaseModel):
    class_id: int
    class_name: str
    course_id: int
    course_name: str
    semester_id: int
    student_count: int
    avg_score: float
    max_score: float
    min_score: float
    ultra_low_rate: float   # < 30
    low_rate: float         # < 40
    pass_rate: float        # >= 60
    good_rate: float        # >= 70
    excellent_rate: float   # >= 85
    distribution: list[ScoreDistributionBucket]


# ── Class-course ranking (single subject) ────────────────────────────────────

class ClassRankingItem(BaseModel):
    rank: int
    student_id: int
    student_no: str
    student_name: str
    score: float

class ClassRankingResponse(BaseModel):
    items: list[ClassRankingItem]
    total: int
    page: int
    page_size: int


# ── Grade ranking (total score across subjects) ─────────────────────────────

class GradeRankingSubjectScore(BaseModel):
    course_id: int
    course_name: str
    score: float

class GradeRankingItem(BaseModel):
    rank: int
    student_id: int
    student_no: str
    student_name: str
    class_name: str
    total_score: float
    subjects: list[GradeRankingSubjectScore]

class GradeRankingResponse(BaseModel):
    items: list[GradeRankingItem]
    total: int
    page: int
    page_size: int


# ── Student personal statistics ──────────────────────────────────────────────

class StudentSubjectStat(BaseModel):
    course_id: int
    course_name: str
    score: float
    class_rank: int
    class_total: int
    grade_rank: int
    grade_total: int
    class_avg: float

class StudentStatisticsResponse(BaseModel):
    student_id: int
    student_no: str
    student_name: str
    class_name: str
    semester_id: int
    subjects: list[StudentSubjectStat]
    total_score: float
    total_class_rank: int
    total_grade_rank: int


# ── Score trend (multi-semester) ─────────────────────────────────────────────

class TrendPoint(BaseModel):
    semester_id: int
    semester_name: str
    student_score: float | None
    class_avg: float | None

class ScoreTrendResponse(BaseModel):
    course_id: int
    course_name: str
    trend: list[TrendPoint]


# ── Cross-class comparison within a grade ────────────────────────────────────

class ClassComparisonItem(BaseModel):
    class_id: int
    class_name: str
    avg_score: float
    pass_rate: float
    excellent_rate: float
    student_count: int

class GradeComparisonResponse(BaseModel):
    course_id: int
    course_name: str
    semester_id: int
    classes: list[ClassComparisonItem]
