# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A student score management system (学生成绩管理系统) with a **FastAPI backend** and **Vue 3 + TypeScript frontend**, containerized with Docker.

## Commands

### Backend (Python / FastAPI)

```bash
cd backend

# Install dependencies
pip install -r requirements-dev.txt  # includes test tools

# Run development server (with auto-reload)
uvicorn app.main:app --reload
# → http://localhost:8000 | Swagger: http://localhost:8000/docs

# Run tests
pytest                          # all tests
pytest tests/test_scores.py    # single module
pytest --cov                   # with coverage report

# Database migrations
alembic upgrade head            # apply all migrations
alembic revision --autogenerate -m "description"  # generate from model changes
alembic downgrade -1            # rollback one step
```

### Frontend (Vue 3 / Vite)

```bash
cd frontend

# Install dependencies
npm install

# Development server (proxies /api → localhost:8000)
npm run dev
# → http://localhost:5173

# Build for production
npm run build

# Testing
npm run test            # Vitest suite
npm run test:coverage   # coverage (80% threshold enforced)

# Code quality
npm run lint            # ESLint
npm run type-check      # TypeScript validation
```

### Docker

```bash
# Full production stack (PostgreSQL + FastAPI + Nginx)
docker-compose up

# Dev mode (DB only — run backend/frontend locally)
docker-compose -f docker-compose.dev.yml up db
```

## Architecture

### Backend Structure

```
backend/app/
├── api/          # Route handlers (auth, users, base_data, scores, health)
├── core/         # Config, database, security, dependencies
├── models/       # SQLAlchemy ORM models (9 entity types)
├── schemas/      # Pydantic request/response schemas
├── services/     # Business logic (score_service, base_data_service, user_service)
└── main.py       # FastAPI entry point, router registration, CORS
```

All API endpoints are versioned under `/api/v1/*`. Five routers are registered in `main.py`: `health`, `auth`, `users`, `base_data`, `scores`.

### Frontend Structure

```
frontend/src/
├── api/          # Axios HTTP client with JWT interceptors
├── components/   # Reusable Vue components
├── router/       # Vue Router with auth guards
├── stores/       # Pinia state (auth store persisted to localStorage)
├── utils/        # Utility functions
└── views/        # Page components (LoginView, LayoutView, DashboardView)
```

### Key Architectural Patterns

**Authentication Flow**: JWT tokens (8-hour expiry) issued at `POST /api/v1/auth/login`. Token stored in `localStorage` via Pinia auth store. Axios request interceptor auto-injects `Authorization: Bearer {token}`. 401 responses redirect to `/login`.

**RBAC (Role-Based Access Control)**:
- `ADMIN` — full system access
- `TEACHER` — read base data; write/modify scores only for their assigned course/class/semester (enforced via `TeacherCourseClass` table)
- `STUDENT` — read own scores only

**Score Audit Logging**: Every score create/update writes a `ScoreAuditLog` record with `old_score`, `new_score`, `changed_by`, `action`, `reason`, and `changed_at`.

**Batch Operations**: `score_service.batch_upsert_scores()` handles atomic multi-score imports. `import_scores_from_excel()` parses `.xlsx` files via OpenPyXL.

**PDF Export**: WeasyPrint + Jinja2 templates render HTML-to-PDF server-side with Chinese font support (fonts installed in Dockerfile).

### Data Model Relationships

`Grade` → `Class` → `Student` ↔ `User`
`Teacher (User)` ↔ `TeacherCourseClass` ↔ `Course` + `Class` + `Semester`
`Score`: composite unique key `(student_id, course_id, semester_id)`, references `Teacher` and `Student`

### Environment Configuration

Backend reads from `.env` (copy `.env.example`). Key variables:
- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — JWT signing key
- `CORS_ORIGINS` — allowed frontend origins
- `ACCESS_TOKEN_EXPIRE_MINUTES` — default 480 (8 hours)

Frontend dev proxy is configured in `vite.config.ts`: `/api` → `http://localhost:8000`.

### Testing Strategy

Backend tests in `backend/tests/` cover auth, users, base data CRUD, score operations, and audit logs using `pytest` + `pytest-asyncio`.

Frontend tests in `frontend/src/__tests__/` use Vitest + Vue Test Utils. Coverage threshold is **80%** on lines, functions, branches, and statements (enforced in `vite.config.ts`).
