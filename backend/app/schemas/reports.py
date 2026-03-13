"""Phase 5.3/5.4: Report generation schemas."""
from pydantic import BaseModel


class BatchTranscriptRequest(BaseModel):
    class_id: int
    semester_id: int
