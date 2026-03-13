"""Phase 5.1: Statistics service — class/grade/student/trend/comparison queries."""
from decimal import Decimal

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.class_ import Class
from app.models.course import Course
from app.models.score import Score
from app.models.semester import Semester
from app.models.student import Student


# ── Distribution helpers ─────────────────────────────────────────────────────

_DISTRIBUTION_BUCKETS = [
    ("<30", Decimal("0"), Decimal("30")),
    ("30-39", Decimal("30"), Decimal("40")),
    ("40-59", Decimal("40"), Decimal("60")),
    ("60-69", Decimal("60"), Decimal("70")),
    ("70-84", Decimal("70"), Decimal("85")),
    ("85-100", Decimal("85"), Decimal("100.1")),
    ("100-150", Decimal("100.1"), Decimal("150.1")),
]


def _build_distribution(scores: list[Decimal]) -> list[dict]:
    result = []
    for label, lo, hi in _DISTRIBUTION_BUCKETS:
        count = sum(1 for s in scores if lo <= s < hi)
        result.append({"range": label, "count": count})
    return result


def _rate(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(count / total * 100, 1)


# ── 1. Class-course statistics ───────────────────────────────────────────────

def class_course_statistics(
    db: Session, class_id: int, course_id: int, semester_id: int,
) -> dict:
    rows = (
        db.query(Score.score)
        .filter(Score.class_id == class_id, Score.course_id == course_id, Score.semester_id == semester_id)
        .all()
    )
    scores = [r.score for r in rows]
    total = len(scores)

    if total == 0:
        return None

    cls = db.get(Class, class_id)
    course = db.get(Course, course_id)

    avg_score = round(float(sum(scores)) / total, 1)
    max_score = float(max(scores))
    min_score = float(min(scores))

    ultra_low = sum(1 for s in scores if s < 30)
    low = sum(1 for s in scores if s < 40)
    pass_count = sum(1 for s in scores if s >= 60)
    good = sum(1 for s in scores if s >= 70)
    excellent = sum(1 for s in scores if s >= 85)

    return {
        "class_id": class_id,
        "class_name": cls.name,
        "course_id": course_id,
        "course_name": course.name,
        "semester_id": semester_id,
        "student_count": total,
        "avg_score": avg_score,
        "max_score": max_score,
        "min_score": min_score,
        "ultra_low_rate": _rate(ultra_low, total),
        "low_rate": _rate(low, total),
        "pass_rate": _rate(pass_count, total),
        "good_rate": _rate(good, total),
        "excellent_rate": _rate(excellent, total),
        "distribution": _build_distribution(scores),
    }


# ── 2. Class ranking (single subject) ────────────────────────────────────────

def class_ranking(
    db: Session, class_id: int, course_id: int, semester_id: int,
    page: int = 1, page_size: int = 50,
) -> tuple[list[dict], int]:
    q = (
        db.query(Score, Student)
        .join(Student, Score.student_id == Student.id)
        .filter(Score.class_id == class_id, Score.course_id == course_id, Score.semester_id == semester_id)
        .order_by(Score.score.desc())
    )
    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()

    # Calculate rank considering offset
    offset = (page - 1) * page_size
    items = []
    for idx, (score_obj, stu) in enumerate(rows):
        items.append({
            "rank": offset + idx + 1,
            "student_id": stu.id,
            "student_no": stu.student_no,
            "student_name": stu.name,
            "score": float(score_obj.score),
        })
    return items, total


# ── 3. Grade ranking (total score across subjects) ──────────────────────────

def grade_ranking(
    db: Session, grade_id: int, semester_id: int,
    page: int = 1, page_size: int = 50,
) -> tuple[list[dict], int]:
    # Get all students in this grade
    students = (
        db.query(Student)
        .join(Class, Student.class_id == Class.id)
        .filter(Class.grade_id == grade_id)
        .all()
    )
    if not students:
        return [], 0

    student_ids = [s.id for s in students]
    student_map = {s.id: s for s in students}
    class_map = {c.id: c.name for c in db.query(Class).filter(Class.grade_id == grade_id).all()}

    # Fetch all scores for these students in the semester
    scores = (
        db.query(Score)
        .filter(Score.student_id.in_(student_ids), Score.semester_id == semester_id)
        .all()
    )

    # Collect course names
    course_ids = {s.course_id for s in scores}
    courses = {c.id: c.name for c in db.query(Course).filter(Course.id.in_(course_ids)).all()} if course_ids else {}

    # Group scores by student
    student_scores: dict[int, list] = {}
    for s in scores:
        student_scores.setdefault(s.student_id, []).append(s)

    # Build ranking entries
    entries = []
    for sid, score_list in student_scores.items():
        stu = student_map[sid]
        total = float(sum(s.score for s in score_list))
        subjects = [
            {"course_id": s.course_id, "course_name": courses.get(s.course_id, ""), "score": float(s.score)}
            for s in score_list
        ]
        entries.append({
            "student_id": sid,
            "student_no": stu.student_no,
            "student_name": stu.name,
            "class_name": class_map.get(stu.class_id, ""),
            "total_score": total,
            "subjects": subjects,
        })

    # Sort by total descending, assign rank
    entries.sort(key=lambda e: e["total_score"], reverse=True)
    for idx, entry in enumerate(entries):
        entry["rank"] = idx + 1

    total_count = len(entries)
    page_entries = entries[(page - 1) * page_size: page * page_size]
    return page_entries, total_count


# ── 4. Student personal statistics ──────────────────────────────────────────

def student_statistics(db: Session, student_id: int, semester_id: int) -> dict | None:
    student = db.get(Student, student_id)
    if not student:
        return None

    cls = db.get(Class, student.class_id)
    grade_id = cls.grade.id if cls.grade else None

    # Student's scores for this semester
    my_scores = (
        db.query(Score)
        .filter(Score.student_id == student_id, Score.semester_id == semester_id)
        .all()
    )
    if not my_scores:
        return None

    course_ids = [s.course_id for s in my_scores]
    courses = {c.id: c.name for c in db.query(Course).filter(Course.id.in_(course_ids)).all()}

    # For each subject, compute class rank and grade rank
    subjects = []
    for sc in my_scores:
        # Class rank
        class_scores = (
            db.query(Score.score)
            .filter(Score.class_id == student.class_id, Score.course_id == sc.course_id, Score.semester_id == semester_id)
            .all()
        )
        class_vals = sorted([float(r.score) for r in class_scores], reverse=True)
        class_rank = class_vals.index(float(sc.score)) + 1

        # Class avg
        class_avg = round(sum(class_vals) / len(class_vals), 1) if class_vals else 0.0

        # Grade rank
        grade_students = (
            db.query(Student.id)
            .join(Class, Student.class_id == Class.id)
            .filter(Class.grade_id == grade_id)
            .subquery()
        )
        grade_scores = (
            db.query(Score.score)
            .filter(Score.student_id.in_(db.query(grade_students.c.id)), Score.course_id == sc.course_id, Score.semester_id == semester_id)
            .all()
        )
        grade_vals = sorted([float(r.score) for r in grade_scores], reverse=True)
        grade_rank = grade_vals.index(float(sc.score)) + 1

        subjects.append({
            "course_id": sc.course_id,
            "course_name": courses.get(sc.course_id, ""),
            "score": float(sc.score),
            "class_rank": class_rank,
            "class_total": len(class_vals),
            "grade_rank": grade_rank,
            "grade_total": len(grade_vals),
            "class_avg": class_avg,
        })

    total_score = sum(s["score"] for s in subjects)

    # Total class rank (sum of all subjects)
    classmates = (
        db.query(Student.id)
        .filter(Student.class_id == student.class_id)
        .all()
    )
    classmate_ids = [c.id for c in classmates]
    classmate_totals = []
    for cid in classmate_ids:
        total = sum(
            float(s.score)
            for s in db.query(Score.score).filter(
                Score.student_id == cid, Score.semester_id == semester_id, Score.course_id.in_(course_ids)
            ).all()
        )
        classmate_totals.append(total)
    classmate_totals.sort(reverse=True)
    total_class_rank = classmate_totals.index(total_score) + 1

    # Total grade rank
    grade_student_ids = [
        r.id for r in db.query(Student.id)
        .join(Class, Student.class_id == Class.id)
        .filter(Class.grade_id == grade_id)
        .all()
    ]
    grade_totals = []
    for gid in grade_student_ids:
        total = sum(
            float(s.score)
            for s in db.query(Score.score).filter(
                Score.student_id == gid, Score.semester_id == semester_id, Score.course_id.in_(course_ids)
            ).all()
        )
        if total > 0:
            grade_totals.append(total)
    grade_totals.sort(reverse=True)
    total_grade_rank = grade_totals.index(total_score) + 1

    return {
        "student_id": student_id,
        "student_no": student.student_no,
        "student_name": student.name,
        "class_name": cls.name,
        "semester_id": semester_id,
        "subjects": subjects,
        "total_score": total_score,
        "total_class_rank": total_class_rank,
        "total_grade_rank": total_grade_rank,
    }


# ── 5. Score trend (multi-semester) ─────────────────────────────────────────

def score_trend(db: Session, student_id: int, course_id: int) -> dict | None:
    student = db.get(Student, student_id)
    if not student:
        return None

    course = db.get(Course, course_id)
    if not course:
        return None

    # All semesters where this student has a score for this course
    semesters = (
        db.query(Semester)
        .join(Score, Score.semester_id == Semester.id)
        .filter(Score.student_id == student_id, Score.course_id == course_id)
        .order_by(Semester.start_date)
        .all()
    )

    trend = []
    for sem in semesters:
        # Student's own score
        my_score = (
            db.query(Score.score)
            .filter(Score.student_id == student_id, Score.course_id == course_id, Score.semester_id == sem.id)
            .scalar()
        )

        # Class average for this course/semester
        class_avg_val = (
            db.query(func.avg(Score.score))
            .filter(Score.class_id == student.class_id, Score.course_id == course_id, Score.semester_id == sem.id)
            .scalar()
        )

        trend.append({
            "semester_id": sem.id,
            "semester_name": sem.name,
            "student_score": float(my_score) if my_score is not None else None,
            "class_avg": round(float(class_avg_val), 1) if class_avg_val is not None else None,
        })

    return {
        "course_id": course_id,
        "course_name": course.name,
        "trend": trend,
    }


# ── 6. Grade comparison (cross-class) ───────────────────────────────────────

def grade_comparison(
    db: Session, grade_id: int, course_id: int, semester_id: int,
) -> dict | None:
    course = db.get(Course, course_id)
    if not course:
        return None

    classes = db.query(Class).filter(Class.grade_id == grade_id).all()
    if not classes:
        return None

    items = []
    for cls in classes:
        scores_rows = (
            db.query(Score.score)
            .filter(Score.class_id == cls.id, Score.course_id == course_id, Score.semester_id == semester_id)
            .all()
        )
        scores = [float(r.score) for r in scores_rows]
        total = len(scores)
        if total == 0:
            continue

        avg = round(sum(scores) / total, 1)
        pass_count = sum(1 for s in scores if s >= 60)
        excellent = sum(1 for s in scores if s >= 85)

        items.append({
            "class_id": cls.id,
            "class_name": cls.name,
            "avg_score": avg,
            "pass_rate": _rate(pass_count, total),
            "excellent_rate": _rate(excellent, total),
            "student_count": total,
        })

    return {
        "course_id": course_id,
        "course_name": course.name,
        "semester_id": semester_id,
        "classes": items,
    }
