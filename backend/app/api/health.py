from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get("/health", tags=["system"])
def health_check(db: Session = Depends(get_db)):
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "database": db_status,
    }
