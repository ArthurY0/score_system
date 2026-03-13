"""Phase 6: Middleware — operation logging, security headers, rate limiting."""
import time
from collections import defaultdict
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.database import SessionLocal

# Overridable session factory — tests replace this with the test DB session factory.
_session_factory = SessionLocal


def set_session_factory(factory):
    global _session_factory
    _session_factory = factory


# ── Operation Log Middleware ─────────────────────────────────────────────────

class OperationLogMiddleware(BaseHTTPMiddleware):
    """Log non-GET requests (POST/PUT/PATCH/DELETE) to operation_logs table."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        if request.method in ("GET", "HEAD", "OPTIONS"):
            return response

        # Extract user info from JWT (best-effort, don't break request if fails)
        user_id = None
        username = None
        try:
            from app.core.security import decode_access_token
            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer "):
                payload = decode_access_token(auth[7:])
                user_id = int(payload.get("sub", 0)) or None
                if user_id:
                    db = _session_factory()
                    try:
                        from app.models.user import User
                        user = db.get(User, user_id)
                        username = user.username if user else None
                    finally:
                        db.close()
        except Exception:
            pass

        # Write log entry
        try:
            db = _session_factory()
            try:
                from app.models.operation_log import OperationLog
                log = OperationLog(
                    user_id=user_id,
                    username=username,
                    method=request.method,
                    path=str(request.url.path),
                    status_code=response.status_code,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                )
                db.add(log)
                db.commit()
            finally:
                db.close()
        except Exception:
            pass  # Never let logging break the request

        return response


# ── Security Headers Middleware ──────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security response headers to all responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


# ── Login Rate Limiting Middleware ───────────────────────────────────────────

class LoginRateLimitMiddleware(BaseHTTPMiddleware):
    """Rate-limit login endpoint: max 10 attempts per IP per 60-second window."""

    # Class-level reference for test access
    _instance = None

    def __init__(self, app, max_attempts: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)
        LoginRateLimitMiddleware._instance = self

    def reset(self):
        self._attempts.clear()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "POST" and request.url.path.rstrip("/").endswith("/auth/login"):
            ip = request.client.host if request.client else "unknown"
            now = time.time()
            # Clean old entries
            self._attempts[ip] = [t for t in self._attempts[ip] if now - t < self.window_seconds]

            if len(self._attempts[ip]) >= self.max_attempts:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "登录尝试过于频繁，请稍后再试"},
                )

            self._attempts[ip].append(now)

        return await call_next(request)
