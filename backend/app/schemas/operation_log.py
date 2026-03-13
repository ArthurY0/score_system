"""Phase 6: Operation log schemas."""
from datetime import datetime

from pydantic import BaseModel


class OperationLogResponse(BaseModel):
    id: int
    user_id: int | None
    username: str | None
    method: str
    path: str
    status_code: int
    ip_address: str | None
    detail: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OperationLogListResponse(BaseModel):
    items: list[OperationLogResponse]
    total: int
    page: int
    page_size: int
