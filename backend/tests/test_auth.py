"""
TDD - Tests written FIRST before implementation.

User Journeys:
  As any user, I want to log in with username/password,
  so that I can get a JWT token and access the system.

  As a logged-in user, I want to fetch my profile,
  so that I know who I am and what role I have.
"""
import pytest
from tests.conftest import auth_header


# ── Login tests ──────────────────────────────────────────────────────────────

def test_login_returns_access_token(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_wrong_password_returns_401(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401


def test_login_with_nonexistent_user_returns_401(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nobody", "password": "any"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401


def test_login_with_inactive_user_returns_401(client, db):
    from app.models.user import User, UserRole
    from app.core.security import hash_password
    inactive = User(
        username="inactive",
        hashed_password=hash_password("pass123"),
        name="停用用户",
        role=UserRole.TEACHER,
        is_active=False,
    )
    db.add(inactive)
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "inactive", "password": "pass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401


# ── /auth/me tests ────────────────────────────────────────────────────────────

def test_me_returns_current_user_info(client, admin_token):
    response = client.get("/api/v1/auth/me", headers=auth_header(admin_token))
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"
    assert "hashed_password" not in data


def test_me_without_token_returns_401(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_invalid_token_returns_401(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this.is.invalid"},
    )
    assert response.status_code == 401
