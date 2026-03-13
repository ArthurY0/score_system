"""Phase 6: System administration endpoints — operation logs, backup info."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_admin
from app.models.operation_log import OperationLog
from app.models.user import User
from app.schemas.operation_log import OperationLogListResponse, OperationLogResponse

router = APIRouter(tags=["system"])


# ── Operation logs ───────────────────────────────────────────────────────────

@router.get("/operation-logs", response_model=OperationLogListResponse)
def list_operation_logs(
    method: str | None = Query(None),
    path: str | None = Query(None),
    username: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(OperationLog)
    if method:
        q = q.filter(OperationLog.method == method.upper())
    if path:
        q = q.filter(OperationLog.path.contains(path))
    if username:
        q = q.filter(OperationLog.username == username)

    total = q.count()
    items = q.order_by(OperationLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return OperationLogListResponse(
        items=[OperationLogResponse.model_validate(log) for log in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── Backup info ──────────────────────────────────────────────────────────────

@router.get("/system/backup-info")
def backup_info(_: User = Depends(require_admin)):
    """Return database backup instructions (no actual backup trigger for safety)."""
    db_url = settings.DATABASE_URL
    # Mask password in URL for display
    masked = db_url
    if "@" in db_url:
        prefix, rest = db_url.split("@", 1)
        if ":" in prefix:
            parts = prefix.rsplit(":", 1)
            masked = f"{parts[0]}:****@{rest}"

    return {
        "database_url_masked": masked,
        "backup_command": "pg_dump -U postgres -h <host> -d score_system > backup_$(date +%Y%m%d_%H%M%S).sql",
        "restore_command": "psql -U postgres -h <host> -d score_system < backup.sql",
        "docker_backup": "docker exec score_db pg_dump -U postgres score_system > backup.sql",
        "recommended_schedule": "每日凌晨 3:00 自动备份，保留最近 30 天",
    }
