import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password

SQLALCHEMY_TEST_DATABASE_URL = "sqlite://"  # in-memory SQLite for tests

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    from app.core.middleware import set_session_factory

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    # Point middleware to test DB
    set_session_factory(TestingSessionLocal)
    # Reset rate limiter between tests
    from app.core.middleware import LoginRateLimitMiddleware
    if LoginRateLimitMiddleware._instance:
        LoginRateLimitMiddleware._instance.reset()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Shared auth fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def admin_user(db):
    from app.models.user import User, UserRole
    user = User(
        username="admin",
        hashed_password=hash_password("admin123"),
        name="管理员",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def teacher_user(db):
    from app.models.user import User, UserRole
    user = User(
        username="teacher1",
        hashed_password=hash_password("teach123"),
        name="张老师",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def student_user(db):
    from app.models.user import User, UserRole
    user = User(
        username="stu001",
        hashed_password=hash_password("stu12345"),
        name="学生甲",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(client, admin_user):
    r = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return r.json()["access_token"]


@pytest.fixture
def teacher_token(client, teacher_user):
    r = client.post(
        "/api/v1/auth/login",
        data={"username": "teacher1", "password": "teach123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return r.json()["access_token"]


@pytest.fixture
def student_token(client, student_user):
    r = client.post(
        "/api/v1/auth/login",
        data={"username": "stu001", "password": "stu12345"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return r.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
