"""
TDD - Tests written FIRST before implementation.

Phase 3: Basic Data Management
Covers: Semesters, Grades, Classes, Courses, Students, TeacherCourseClass

User Journeys:
  As an admin, I want to manage semesters/grades/classes/courses,
  so that the system has the foundational data for score management.

  As an admin, I want to manage student records,
  so that each student's profile is correctly associated with a class.

  As a teacher, I want to view grades/classes/courses I'm assigned to,
  so that I can enter scores for the right students.
"""
import io
from datetime import date
import pytest
from tests.conftest import auth_header


# ═══════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def semester(db):
    from app.models.semester import Semester
    s = Semester(name="2025-2026学年第一学期", start_date=date(2025, 9, 1), end_date=date(2026, 1, 20), is_active=True)
    db.add(s); db.commit(); db.refresh(s)
    return s


@pytest.fixture
def grade(db):
    from app.models.grade import Grade
    g = Grade(name="高一")
    db.add(g); db.commit(); db.refresh(g)
    return g


@pytest.fixture
def class_(db, grade):
    from app.models.class_ import Class
    c = Class(name="高一(1)班", grade_id=grade.id)
    db.add(c); db.commit(); db.refresh(c)
    return c


@pytest.fixture
def course(db):
    from app.models.course import Course
    c = Course(name="数学")
    db.add(c); db.commit(); db.refresh(c)
    return c


@pytest.fixture
def student(db, class_):
    from app.models.student import Student, Gender
    s = Student(student_no="20250101", name="张三", gender=Gender.MALE, class_id=class_.id)
    db.add(s); db.commit(); db.refresh(s)
    return s


@pytest.fixture
def teacher_course_class(db, teacher_user, course, class_, semester):
    from app.models.teacher_course_class import TeacherCourseClass
    tcc = TeacherCourseClass(
        teacher_id=teacher_user.id,
        course_id=course.id,
        class_id=class_.id,
        semester_id=semester.id,
    )
    db.add(tcc); db.commit(); db.refresh(tcc)
    return tcc


# ═══════════════════════════════════════════════════════════
# SEMESTER TESTS
# ═══════════════════════════════════════════════════════════

class TestSemesters:
    def test_admin_can_list_semesters(self, client, admin_token):
        r = client.get("/api/v1/semesters", headers=auth_header(admin_token))
        assert r.status_code == 200
        assert "items" in r.json()

    def test_teacher_can_list_semesters(self, client, teacher_token, teacher_user):
        r = client.get("/api/v1/semesters", headers=auth_header(teacher_token))
        assert r.status_code == 200

    def test_admin_can_create_semester(self, client, admin_token):
        r = client.post("/api/v1/semesters",
            json={"name": "2026春季学期", "start_date": "2026-02-01", "end_date": "2026-07-10", "is_active": False},
            headers=auth_header(admin_token))
        assert r.status_code == 201
        assert r.json()["name"] == "2026春季学期"

    def test_teacher_cannot_create_semester(self, client, teacher_token, teacher_user):
        r = client.post("/api/v1/semesters",
            json={"name": "X", "start_date": "2026-01-01", "end_date": "2026-06-01", "is_active": False},
            headers=auth_header(teacher_token))
        assert r.status_code == 403

    def test_admin_can_get_semester(self, client, admin_token, semester):
        r = client.get(f"/api/v1/semesters/{semester.id}", headers=auth_header(admin_token))
        assert r.status_code == 200
        assert r.json()["name"] == "2025-2026学年第一学期"

    def test_get_nonexistent_semester_returns_404(self, client, admin_token):
        assert client.get("/api/v1/semesters/99999", headers=auth_header(admin_token)).status_code == 404

    def test_admin_can_update_semester(self, client, admin_token, semester):
        r = client.put(f"/api/v1/semesters/{semester.id}",
            json={"name": "更新学期", "start_date": "2025-09-01", "end_date": "2026-01-20", "is_active": True},
            headers=auth_header(admin_token))
        assert r.status_code == 200
        assert r.json()["name"] == "更新学期"

    def test_admin_can_delete_semester(self, client, admin_token, semester):
        assert client.delete(f"/api/v1/semesters/{semester.id}", headers=auth_header(admin_token)).status_code == 204

    def test_duplicate_semester_name_returns_409(self, client, admin_token, semester):
        r = client.post("/api/v1/semesters",
            json={"name": "2025-2026学年第一学期", "start_date": "2025-09-01", "end_date": "2026-01-20", "is_active": False},
            headers=auth_header(admin_token))
        assert r.status_code == 409


# ═══════════════════════════════════════════════════════════
# GRADE TESTS
# ═══════════════════════════════════════════════════════════

class TestGrades:
    def test_admin_can_list_grades(self, client, admin_token):
        r = client.get("/api/v1/grades", headers=auth_header(admin_token))
        assert r.status_code == 200

    def test_admin_can_create_grade(self, client, admin_token):
        r = client.post("/api/v1/grades", json={"name": "高二"}, headers=auth_header(admin_token))
        assert r.status_code == 201
        assert r.json()["name"] == "高二"

    def test_duplicate_grade_name_returns_409(self, client, admin_token, grade):
        r = client.post("/api/v1/grades", json={"name": "高一"}, headers=auth_header(admin_token))
        assert r.status_code == 409

    def test_admin_can_update_grade(self, client, admin_token, grade):
        r = client.put(f"/api/v1/grades/{grade.id}", json={"name": "高一（更新）"}, headers=auth_header(admin_token))
        assert r.status_code == 200
        assert r.json()["name"] == "高一（更新）"

    def test_admin_can_delete_grade(self, client, admin_token, grade):
        assert client.delete(f"/api/v1/grades/{grade.id}", headers=auth_header(admin_token)).status_code == 204

    def test_teacher_cannot_create_grade(self, client, teacher_token, teacher_user):
        r = client.post("/api/v1/grades", json={"name": "X"}, headers=auth_header(teacher_token))
        assert r.status_code == 403


# ═══════════════════════════════════════════════════════════
# CLASS TESTS
# ═══════════════════════════════════════════════════════════

class TestClasses:
    def test_admin_can_list_classes(self, client, admin_token):
        r = client.get("/api/v1/classes", headers=auth_header(admin_token))
        assert r.status_code == 200

    def test_list_classes_filtered_by_grade(self, client, admin_token, class_, grade):
        r = client.get(f"/api/v1/classes?grade_id={grade.id}", headers=auth_header(admin_token))
        assert r.status_code == 200
        items = r.json()["items"]
        assert any(c["id"] == class_.id for c in items)

    def test_admin_can_create_class(self, client, admin_token, grade):
        r = client.post("/api/v1/classes",
            json={"name": "高一(2)班", "grade_id": grade.id},
            headers=auth_header(admin_token))
        assert r.status_code == 201
        assert r.json()["grade_id"] == grade.id

    def test_create_class_with_invalid_grade_returns_404(self, client, admin_token):
        r = client.post("/api/v1/classes",
            json={"name": "测试班", "grade_id": 99999},
            headers=auth_header(admin_token))
        assert r.status_code == 404

    def test_admin_can_update_class(self, client, admin_token, class_):
        r = client.put(f"/api/v1/classes/{class_.id}",
            json={"name": "高一(1)班（更新）", "grade_id": class_.grade_id},
            headers=auth_header(admin_token))
        assert r.status_code == 200

    def test_admin_can_delete_class(self, client, admin_token, class_):
        assert client.delete(f"/api/v1/classes/{class_.id}", headers=auth_header(admin_token)).status_code == 204

    def test_teacher_cannot_create_class(self, client, teacher_token, teacher_user, grade):
        r = client.post("/api/v1/classes",
            json={"name": "X", "grade_id": grade.id},
            headers=auth_header(teacher_token))
        assert r.status_code == 403


# ═══════════════════════════════════════════════════════════
# COURSE TESTS
# ═══════════════════════════════════════════════════════════

class TestCourses:
    def test_admin_can_list_courses(self, client, admin_token):
        r = client.get("/api/v1/courses", headers=auth_header(admin_token))
        assert r.status_code == 200

    def test_teacher_can_list_courses(self, client, teacher_token, teacher_user):
        assert client.get("/api/v1/courses", headers=auth_header(teacher_token)).status_code == 200

    def test_admin_can_create_course(self, client, admin_token):
        r = client.post("/api/v1/courses", json={"name": "语文"}, headers=auth_header(admin_token))
        assert r.status_code == 201
        assert r.json()["name"] == "语文"

    def test_duplicate_course_name_returns_409(self, client, admin_token, course):
        r = client.post("/api/v1/courses", json={"name": "数学"}, headers=auth_header(admin_token))
        assert r.status_code == 409

    def test_admin_can_update_course(self, client, admin_token, course):
        r = client.put(f"/api/v1/courses/{course.id}", json={"name": "高等数学"}, headers=auth_header(admin_token))
        assert r.status_code == 200

    def test_admin_can_delete_course(self, client, admin_token, course):
        assert client.delete(f"/api/v1/courses/{course.id}", headers=auth_header(admin_token)).status_code == 204

    def test_teacher_cannot_create_course(self, client, teacher_token, teacher_user):
        r = client.post("/api/v1/courses", json={"name": "X"}, headers=auth_header(teacher_token))
        assert r.status_code == 403


# ═══════════════════════════════════════════════════════════
# STUDENT TESTS
# ═══════════════════════════════════════════════════════════

class TestStudents:
    def test_admin_can_list_students(self, client, admin_token):
        r = client.get("/api/v1/students", headers=auth_header(admin_token))
        assert r.status_code == 200

    def test_list_students_filtered_by_class(self, client, admin_token, student, class_):
        r = client.get(f"/api/v1/students?class_id={class_.id}", headers=auth_header(admin_token))
        items = r.json()["items"]
        assert any(s["student_no"] == "20250101" for s in items)

    def test_admin_can_create_student(self, client, admin_token, class_):
        r = client.post("/api/v1/students",
            json={"student_no": "20250102", "name": "李四", "gender": "female", "class_id": class_.id},
            headers=auth_header(admin_token))
        assert r.status_code == 201
        assert r.json()["student_no"] == "20250102"

    def test_duplicate_student_no_returns_409(self, client, admin_token, student, class_):
        r = client.post("/api/v1/students",
            json={"student_no": "20250101", "name": "重复", "gender": "male", "class_id": class_.id},
            headers=auth_header(admin_token))
        assert r.status_code == 409

    def test_create_student_with_invalid_class_returns_404(self, client, admin_token):
        r = client.post("/api/v1/students",
            json={"student_no": "99990001", "name": "无效班级", "gender": "male", "class_id": 99999},
            headers=auth_header(admin_token))
        assert r.status_code == 404

    def test_admin_can_get_student(self, client, admin_token, student):
        r = client.get(f"/api/v1/students/{student.id}", headers=auth_header(admin_token))
        assert r.status_code == 200
        assert r.json()["student_no"] == "20250101"

    def test_admin_can_update_student(self, client, admin_token, student, class_):
        r = client.put(f"/api/v1/students/{student.id}",
            json={"student_no": "20250101", "name": "张三（更新）", "gender": "male", "class_id": class_.id},
            headers=auth_header(admin_token))
        assert r.status_code == 200
        assert r.json()["name"] == "张三（更新）"

    def test_admin_can_delete_student(self, client, admin_token, student):
        assert client.delete(f"/api/v1/students/{student.id}", headers=auth_header(admin_token)).status_code == 204

    def test_teacher_cannot_create_student(self, client, teacher_token, teacher_user, class_):
        r = client.post("/api/v1/students",
            json={"student_no": "X001", "name": "X", "gender": "male", "class_id": class_.id},
            headers=auth_header(teacher_token))
        assert r.status_code == 403

    def test_admin_can_import_students_via_excel(self, client, admin_token, class_):
        """Excel bulk import: must accept a valid xlsx and create students."""
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["学号", "姓名", "性别", "班级ID"])
        ws.append(["20250201", "王五", "男", class_.id])
        ws.append(["20250202", "赵六", "女", class_.id])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        r = client.post(
            "/api/v1/students/import",
            files={"file": ("students.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            headers=auth_header(admin_token),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["created"] == 2
        assert data["errors"] == []

    def test_excel_import_reports_duplicate_student_no(self, client, admin_token, class_, student):
        """Excel import should skip duplicates and report them as errors."""
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["学号", "姓名", "性别", "班级ID"])
        ws.append(["20250101", "重复学号", "男", class_.id])  # already exists
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        r = client.post(
            "/api/v1/students/import",
            files={"file": ("students.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            headers=auth_header(admin_token),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["created"] == 0
        assert len(data["errors"]) == 1


# ═══════════════════════════════════════════════════════════
# TEACHER-COURSE-CLASS ASSIGNMENT TESTS
# ═══════════════════════════════════════════════════════════

class TestTeacherCourseClass:
    def test_admin_can_assign_teacher_to_course_class(self, client, admin_token, teacher_user, course, class_, semester):
        r = client.post("/api/v1/assignments",
            json={
                "teacher_id": teacher_user.id,
                "course_id": course.id,
                "class_id": class_.id,
                "semester_id": semester.id,
            },
            headers=auth_header(admin_token))
        assert r.status_code == 201

    def test_admin_can_list_assignments(self, client, admin_token, teacher_course_class):
        r = client.get("/api/v1/assignments", headers=auth_header(admin_token))
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_duplicate_assignment_returns_409(self, client, admin_token, teacher_course_class, teacher_user, course, class_, semester):
        r = client.post("/api/v1/assignments",
            json={
                "teacher_id": teacher_user.id,
                "course_id": course.id,
                "class_id": class_.id,
                "semester_id": semester.id,
            },
            headers=auth_header(admin_token))
        assert r.status_code == 409

    def test_admin_can_delete_assignment(self, client, admin_token, teacher_course_class):
        r = client.delete(f"/api/v1/assignments/{teacher_course_class.id}", headers=auth_header(admin_token))
        assert r.status_code == 204

    def test_teacher_can_view_own_assignments(self, client, teacher_token, teacher_course_class, teacher_user):
        r = client.get(f"/api/v1/assignments?teacher_id={teacher_user.id}", headers=auth_header(teacher_token))
        assert r.status_code == 200
