"""Phase 6: Operation log + system hardening tests — TDD RED phase."""
import pytest

from tests.conftest import auth_header


# ── 1. Operation log middleware ──────────────────────────────────────────────

class TestOperationLogMiddleware:
    def test_records_write_operations(self, client, admin_token, db):
        """POST/PUT/DELETE operations should create log entries."""
        from app.models.operation_log import OperationLog

        # Trigger a POST operation
        client.post(
            "/api/v1/courses",
            json={"name": "日志测试课程"},
            headers=auth_header(admin_token),
        )

        logs = db.query(OperationLog).filter(OperationLog.path.like("%courses%")).all()
        assert len(logs) >= 1
        log = logs[-1]
        assert log.method == "POST"
        assert log.status_code == 201
        assert log.username == "admin"

    def test_does_not_log_get_requests(self, client, admin_token, db):
        """GET requests should NOT be logged (too noisy)."""
        from app.models.operation_log import OperationLog

        before = db.query(OperationLog).count()
        client.get("/api/v1/health", headers=auth_header(admin_token))
        after = db.query(OperationLog).count()
        assert after == before

    def test_logs_include_ip_and_user_agent(self, client, admin_token, db):
        from app.models.operation_log import OperationLog

        client.post(
            "/api/v1/courses",
            json={"name": "IP测试课程"},
            headers={**auth_header(admin_token), "User-Agent": "TestBot/1.0"},
        )

        log = db.query(OperationLog).order_by(OperationLog.id.desc()).first()
        assert log.ip_address is not None
        assert log.user_agent == "TestBot/1.0"

    def test_logs_failed_operations(self, client, admin_token, db):
        """Failed operations (4xx/5xx) should also be logged."""
        from app.models.operation_log import OperationLog

        client.post(
            "/api/v1/courses",
            json={"name": "日志测试课程2"},
            headers=auth_header(admin_token),
        )
        # Duplicate → 409
        client.post(
            "/api/v1/courses",
            json={"name": "日志测试课程2"},
            headers=auth_header(admin_token),
        )

        logs = db.query(OperationLog).filter(
            OperationLog.path.like("%courses%"),
            OperationLog.status_code >= 400,
        ).all()
        assert len(logs) >= 1


# ── 2. Operation log query API ──────────────────────────────────────────────

class TestOperationLogApi:
    def test_admin_can_list_logs(self, client, admin_token, db):
        # Create some log entries first
        client.post(
            "/api/v1/courses",
            json={"name": "查询日志课程"},
            headers=auth_header(admin_token),
        )

        r = client.get(
            "/api/v1/operation-logs",
            headers=auth_header(admin_token),
        )
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert body["total"] >= 1

    def test_admin_can_filter_by_method(self, client, admin_token, db):
        client.post(
            "/api/v1/courses",
            json={"name": "过滤日志课程"},
            headers=auth_header(admin_token),
        )

        r = client.get(
            "/api/v1/operation-logs",
            params={"method": "POST"},
            headers=auth_header(admin_token),
        )
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["method"] == "POST"

    def test_teacher_forbidden(self, client, teacher_token):
        r = client.get("/api/v1/operation-logs", headers=auth_header(teacher_token))
        assert r.status_code == 403

    def test_student_forbidden(self, client, student_token):
        r = client.get("/api/v1/operation-logs", headers=auth_header(student_token))
        assert r.status_code == 403


# ── 3. Security headers middleware ──────────────────────────────────────────

class TestSecurityHeaders:
    def test_has_x_content_type_options(self, client):
        r = client.get("/api/v1/health")
        assert r.headers.get("x-content-type-options") == "nosniff"

    def test_has_x_frame_options(self, client):
        r = client.get("/api/v1/health")
        assert r.headers.get("x-frame-options") == "DENY"

    def test_has_referrer_policy(self, client):
        r = client.get("/api/v1/health")
        assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


# ── 4. Rate limiting (login) ────────────────────────────────────────────────

class TestRateLimiting:
    def test_login_rate_limit(self, client, admin_user):
        """After many failed login attempts, should be rate-limited."""
        for _ in range(12):
            client.post(
                "/api/v1/auth/login",
                data={"username": "admin", "password": "wrong"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        r = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "wrong"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert r.status_code == 429


# ── 5. Backup API ───────────────────────────────────────────────────────────

class TestBackupApi:
    def test_admin_can_trigger_backup_info(self, client, admin_token):
        r = client.get("/api/v1/system/backup-info", headers=auth_header(admin_token))
        assert r.status_code == 200
        body = r.json()
        assert "database_url_masked" in body
        assert "backup_command" in body

    def test_teacher_forbidden(self, client, teacher_token):
        r = client.get("/api/v1/system/backup-info", headers=auth_header(teacher_token))
        assert r.status_code == 403


# ── 6. Composite index presence ─────────────────────────────────────────────

class TestCompositeIndex:
    def test_scores_composite_index_exists(self, db):
        """The scores table should have a composite index on (semester_id, class_id, course_id)."""
        from app.models.score import Score
        indexes = Score.__table__.indexes
        col_sets = [frozenset(c.name for c in idx.columns) for idx in indexes]
        expected = frozenset(["semester_id", "class_id", "course_id"])
        assert expected in col_sets, f"Missing composite index. Found: {col_sets}"
