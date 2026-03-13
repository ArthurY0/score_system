from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import LoginRateLimitMiddleware, OperationLogMiddleware, SecurityHeadersMiddleware
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.base_data import (
    semesters_router, grades_router, classes_router,
    courses_router, students_router, assignments_router,
)
from app.api.scores import router as scores_router
from app.api.statistics import router as statistics_router
from app.api.reports import router as reports_router
from app.api.system import router as system_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware (order matters: outermost first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(OperationLogMiddleware)
app.add_middleware(LoginRateLimitMiddleware, max_attempts=10, window_seconds=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(semesters_router, prefix="/api/v1")
app.include_router(grades_router, prefix="/api/v1")
app.include_router(classes_router, prefix="/api/v1")
app.include_router(courses_router, prefix="/api/v1")
app.include_router(students_router, prefix="/api/v1")
app.include_router(assignments_router, prefix="/api/v1")
app.include_router(scores_router, prefix="/api/v1")
app.include_router(statistics_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
def root():
    return {"message": f"Welcome to {settings.APP_NAME}", "docs": "/docs"}
