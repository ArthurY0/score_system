"""Phase 5.1: Statistics API tests — TDD RED phase.

Tests cover all 6 statistics endpoints with RBAC enforcement.
"""
from datetime import date
from decimal import Decimal

import pytest

from tests.conftest import auth_header


# ── Shared fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def seed_data(db):
    """Create a full hierarchy: grade → class → students → semester → course → assignment → scores."""
    from app.core.security import hash_password
    from app.models.class_ import Class
    from app.models.course import Course
    from app.models.grade import Grade
    from app.models.score import Score
    from app.models.semester import Semester
    from app.models.student import Student
    from app.models.teacher_course_class import TeacherCourseClass
    from app.models.user import User, UserRole

    # Teacher
    teacher = User(username="t1", hashed_password=hash_password("t12345"), name="王老师", role=UserRole.TEACHER, is_active=True)
    db.add(teacher)
    db.flush()

    # Grade & two classes
    grade = Grade(name="高一")
    db.add(grade)
    db.flush()

    cls_a = Class(name="高一(1)班", grade_id=grade.id)
    cls_b = Class(name="高一(2)班", grade_id=grade.id)
    db.add_all([cls_a, cls_b])
    db.flush()

    # Semester
    sem = Semester(name="2025-2026第一学期", start_date=date(2025, 9, 1), end_date=date(2026, 1, 31), is_active=True)
    db.add(sem)
    db.flush()

    # Second semester for trend tests
    sem2 = Semester(name="2025-2026第二学期", start_date=date(2026, 2, 1), end_date=date(2026, 6, 30), is_active=False)
    db.add(sem2)
    db.flush()

    # Course
    math = Course(name="数学")
    db.add(math)
    db.flush()

    # Assignment
    assign_a = TeacherCourseClass(teacher_id=teacher.id, course_id=math.id, class_id=cls_a.id, semester_id=sem.id)
    assign_b = TeacherCourseClass(teacher_id=teacher.id, course_id=math.id, class_id=cls_b.id, semester_id=sem.id)
    db.add_all([assign_a, assign_b])
    db.flush()

    # Students in class A (5 students with varied scores)
    students_a = []
    scores_a = [Decimal("95"), Decimal("72"), Decimal("58"), Decimal("35"), Decimal("25")]
    for i, sc in enumerate(scores_a, start=1):
        stu = Student(student_no=f"A{i:03d}", name=f"学生A{i}", gender="male", class_id=cls_a.id)
        db.add(stu)
        db.flush()
        students_a.append(stu)
        db.add(Score(student_id=stu.id, course_id=math.id, class_id=cls_a.id, semester_id=sem.id, teacher_id=teacher.id, score=sc))

    # Students in class B (3 students)
    students_b = []
    scores_b = [Decimal("88"), Decimal("66"), Decimal("42")]
    for i, sc in enumerate(scores_b, start=1):
        stu = Student(student_no=f"B{i:03d}", name=f"学生B{i}", gender="female", class_id=cls_b.id)
        db.add(stu)
        db.flush()
        students_b.append(stu)
        db.add(Score(student_id=stu.id, course_id=math.id, class_id=cls_b.id, semester_id=sem.id, teacher_id=teacher.id, score=sc))

    # Semester 2 scores for student A1 (trend test)
    db.add(Score(student_id=students_a[0].id, course_id=math.id, class_id=cls_a.id, semester_id=sem2.id, teacher_id=teacher.id, score=Decimal("90")))

    db.commit()

    return {
        "teacher": teacher,
        "grade": grade,
        "cls_a": cls_a, "cls_b": cls_b,
        "sem": sem, "sem2": sem2,
        "math": math,
        "students_a": students_a,
        "students_b": students_b,
    }


@pytest.fixture
def teacher_tok(client, seed_data):
    r = client.post("/api/v1/auth/login", data={"username": "t1", "password": "t12345"}, headers={"Content-Type": "application/x-www-form-urlencoded"})
    return r.json()["access_token"]


# ── 1. Class-course statistics ───────────────────────────────────────────────

class TestClassCourseStatistics:
    def test_returns_statistics(self, client, teacher_tok, seed_data):
        d = seed_data
        r = client.get(
            "/api/v1/statistics/class-course",
            params={"class_id": d["cls_a"].id, "course_id": d["math"].id, "semester_id": d["sem"].id},
            headers=auth_header(teacher_tok),
        )
        assert r.status_code == 200
        body = r.json()
        assert body["student_count"] == 5
        assert body["max_score"] == 95.0
        assert body["min_score"] == 25.0
        # avg = (95+72+58+35+25)/5 = 57.0
        assert body["avg_score"] == 57.0
        # ultra_low (<30): 1/5 = 20%
        assert body["ultra_low_rate"] == 20.0
        # low (<40): 2/5 = 40%  (25 and 35)
        assert body["low_rate"] == 40.0
        # pass (>=60): 2/5 = 40%  (95 and 72)
        assert body["pass_rate"] == 40.0
        # good (>=70): 2/5 = 40%
        assert body["good_rate"] == 40.0
        # excellent (>=85): 1/5 = 20%
        assert body["excellent_rate"] == 20.0

    def test_distribution_buckets(self, client, teacher_tok, seed_data):
        d = seed_data
        r = client.get(
            "/api/v1/statistics/class-course",
            params={"class_id": d["cls_a"].id, "course_id": d["math"].id, "semester_id": d["sem"].id},
            headers=auth_header(teacher_tok),
        )
        buckets = {b["range"]: b["count"] for b in r.json()["distribution"]}
        assert buckets["<30"] == 1      # 25
        assert buckets["30-39"] == 1    # 35
        assert buckets["40-59"] == 1    # 58
        assert buckets["60-69"] == 0
        assert buckets["70-84"] == 1    # 72
        assert buckets["85-100"] == 1   # 95

    def test_missing_params_returns_422(self, client, teacher_tok):
        r = client.get("/api/v1/statistics/class-course", headers=auth_header(teacher_tok))
        assert r.status_code == 422

    def test_student_forbidden(self, client, student_token):
        r = client.get(
            "/api/v1/statistics/class-course",
            params={"class_id": 1, "course_id": 1, "semester_id": 1},
            headers=auth_header(student_token),
        )
        assert r.status_code == 403


# ── 2. Class ranking (single subject) ────────────────────────────────────────

class TestClassRanking:
    def test_returns_ranked_list(self, client, teacher_tok, seed_data):
        d = seed_data
        r = client.get(
            "/api/v1/statistics/class-ranking",
            params={"class_id": d["cls_a"].id, "course_id": d["math"].id, "semester_id": d["sem"].id},
            headers=auth_header(teacher_tok),
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 5
        # First rank should be highest score
        assert items[0]["score"] == 95.0
        assert items[0]["rank"] == 1
        # Verify descending order
        scores = [it["score"] for it in items]
        assert scores == sorted(scores, reverse=True)

    def test_pagination(self, client, teacher_tok, seed_data):
        d = seed_data
        r = client.get(
            "/api/v1/statistics/class-ranking",
            params={"class_id": d["cls_a"].id, "course_id": d["math"].id, "semester_id": d["sem"].id, "page": 1, "page_size": 2},
            headers=auth_header(teacher_tok),
        )
        body = r.json()
        assert len(body["items"]) == 2
        assert body["total"] == 5


# ── 3. Grade ranking (total score) ──────────────────────────────────────────

class TestGradeRanking:
    def test_returns_all_students_in_grade(self, client, teacher_tok, seed_data):
        d = seed_data
        r = client.get(
            "/api/v1/statistics/grade-ranking",
            params={"grade_id": d["grade"].id, "semester_id": d["sem"].id},
            headers=auth_header(teacher_tok),
        )
        assert r.status_code == 200
        body = r.json()
        # 5 students in cls_a + 3 in cls_b = 8
        assert body["total"] == 8
        items = body["items"]
        # First should be highest total
        assert items[0]["total_score"] == 95.0  # student A1
        assert items[0]["rank"] == 1
        # Each item should have subjects list
        assert len(items[0]["subjects"]) >= 1

    def test_includes_class_name(self, client, teacher_tok, seed_data):
        d = seed_data
        r = client.get(
            "/api/v1/statistics/grade-ranking",
            params={"grade_id": d["grade"].id, "semester_id": d["sem"].id},
            headers=auth_header(teacher_tok),
        )
        items = r.json()["items"]
        class_names = {it["class_name"] for it in items}
        assert "高一(1)班" in class_names
        assert "高一(2)班" in class_names


# ── 4. Student personal statistics ───────────────────────────────────────────

class TestStudentStatistics:
    def test_returns_student_stats(self, client, teacher_tok, seed_data):
        d = seed_data
        stu = d["students_a"][0]  # score 95
        r = client.get(
            f"/api/v1/statistics/student/{stu.id}",
            params={"semester_id": d["sem"].id},
            headers=auth_header(teacher_tok),
        )
        assert r.status_code == 200
        body = r.json()
        assert body["student_id"] == stu.id
        assert body["student_name"] == "学生A1"
        assert len(body["subjects"]) == 1
        subj = body["subjects"][0]
        assert subj["score"] == 95.0
        assert subj["class_rank"] == 1  # highest in class A
        assert subj["grade_rank"] == 1  # highest in entire grade

    def test_student_can_view_own_stats(self, client, seed_data, db):
        """A student with a linked user account can view their own statistics."""
        from app.core.security import hash_password
        from app.models.user import User, UserRole

        stu = seed_data["students_a"][0]
        # Create a student user linked to this student
        user = User(username="stua1", hashed_password=hash_password("pass123"), name="学生A1", role=UserRole.STUDENT, is_active=True)
        db.add(user)
        db.flush()
        stu.user_id = user.id
        db.commit()

        r = client.post("/api/v1/auth/login", data={"username": "stua1", "password": "pass123"}, headers={"Content-Type": "application/x-www-form-urlencoded"})
        tok = r.json()["access_token"]

        r = client.get(
            f"/api/v1/statistics/student/{stu.id}",
            params={"semester_id": seed_data["sem"].id},
            headers=auth_header(tok),
        )
        assert r.status_code == 200

    def test_student_cannot_view_other(self, client, seed_data, db):
        """A student cannot view another student's statistics."""
        from app.core.security import hash_password
        from app.models.user import User, UserRole

        other_stu = seed_data["students_a"][1]
        user = User(username="stua_other", hashed_password=hash_password("pass123"), name="其他", role=UserRole.STUDENT, is_active=True)
        db.add(user)
        db.flush()
        # Link user to student A1, but try to view student A2
        seed_data["students_a"][0].user_id = user.id
        db.commit()

        r = client.post("/api/v1/auth/login", data={"username": "stua_other", "password": "pass123"}, headers={"Content-Type": "application/x-www-form-urlencoded"})
        tok = r.json()["access_token"]

        r = client.get(
            f"/api/v1/statistics/student/{other_stu.id}",
            params={"semester_id": seed_data["sem"].id},
            headers=auth_header(tok),
        )
        assert r.status_code == 403

    def test_not_found(self, client, teacher_tok, seed_data):
        r = client.get(
            "/api/v1/statistics/student/9999",
            params={"semester_id": seed_data["sem"].id},
            headers=auth_header(teacher_tok),
        )
        assert r.status_code == 404


# ── 5. Score trend ───────────────────────────────────────────────────────────

class TestScoreTrend:
    def test_returns_multi_semester_trend(self, client, teacher_tok, seed_data):
        d = seed_data
        stu = d["students_a"][0]  # has scores in both semesters
        r = client.get(
            "/api/v1/statistics/trend",
            params={"student_id": stu.id, "course_id": d["math"].id},
            headers=auth_header(teacher_tok),
        )
        assert r.status_code == 200
        body = r.json()
        assert body["course_id"] == d["math"].id
        trend = body["trend"]
        assert len(trend) == 2
        # First semester score
        assert trend[0]["student_score"] == 95.0
        assert trend[0]["class_avg"] is not None
        # Second semester score
        assert trend[1]["student_score"] == 90.0


# ── 6. Grade comparison (cross-class) ───────────────────────────────────────

class TestGradeComparison:
    def test_compares_classes(self, client, teacher_tok, seed_data):
        d = seed_data
        r = client.get(
            "/api/v1/statistics/comparison",
            params={"grade_id": d["grade"].id, "course_id": d["math"].id, "semester_id": d["sem"].id},
            headers=auth_header(teacher_tok),
        )
        assert r.status_code == 200
        body = r.json()
        classes = body["classes"]
        assert len(classes) == 2

        # Find class A and class B
        by_name = {c["class_name"]: c for c in classes}
        ca = by_name["高一(1)班"]
        cb = by_name["高一(2)班"]

        assert ca["student_count"] == 5
        assert cb["student_count"] == 3
        # Class A avg = (95+72+58+35+25)/5 = 57.0
        assert ca["avg_score"] == 57.0
        # Class B avg = (88+66+42)/3 = 65.333...
        assert round(cb["avg_score"], 1) == 65.3

    def test_student_forbidden(self, client, student_token):
        r = client.get(
            "/api/v1/statistics/comparison",
            params={"grade_id": 1, "course_id": 1, "semester_id": 1},
            headers=auth_header(student_token),
        )
        assert r.status_code == 403
