from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ScoreCreate(BaseModel):
    student_id: int
    course_id: int
    class_id: int
    semester_id: int
    score: Decimal = Field(..., ge=0, le=150)


class ScoreUpdate(BaseModel):
    score: Decimal = Field(..., ge=0, le=150)
    reason: str | None = None


class ScoreResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    class_id: int
    semester_id: int
    teacher_id: int
    score: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BatchEntry(BaseModel):
    student_id: int
    score: Decimal = Field(..., ge=0, le=150)


class BatchScoreCreate(BaseModel):
    class_id: int
    course_id: int
    semester_id: int
    teacher_id: int
    entries: list[BatchEntry]


class BatchScoreResult(BaseModel):
    created: int
    updated: int
    errors: list[str]


class ScoreImportResult(BaseModel):
    created: int
    updated: int
    errors: list[str]


class AuditLogResponse(BaseModel):
    id: int
    score_id: int
    old_score: float | None
    new_score: float
    changed_by: int
    changed_at: datetime
    action: str
    reason: str | None

    model_config = {"from_attributes": True}


class ScoreListResponse(BaseModel):
    items: list[ScoreResponse]
    total: int
    page: int
    page_size: int
