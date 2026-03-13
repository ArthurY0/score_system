"""TDD - User management tests."""
from tests.conftest import auth_header


def test_admin_can_list_users(client, admin_token, admin_user):
    response = client.get("/api/v1/users", headers=auth_header(admin_token))
    assert response.status_code == 200
    data = response.json()
    assert "items" in data and "total" in data
    assert data["total"] >= 1


def test_teacher_cannot_list_users(client, teacher_token, teacher_user):
    assert client.get("/api/v1/users", headers=auth_header(teacher_token)).status_code == 403


def test_unauthenticated_cannot_list_users(client):
    assert client.get("/api/v1/users").status_code == 401


def test_admin_can_create_user(client, admin_token):
    r = client.post("/api/v1/users",
        json={"username": "newteacher", "password": "pass1234", "name": "李老师", "role": "teacher"},
        headers=auth_header(admin_token))
    assert r.status_code == 201
    assert r.json()["username"] == "newteacher"
    assert "hashed_password" not in r.json()


def test_create_user_with_duplicate_username_returns_409(client, admin_token, admin_user):
    r = client.post("/api/v1/users",
        json={"username": "admin", "password": "pass1234", "name": "重复", "role": "teacher"},
        headers=auth_header(admin_token))
    assert r.status_code == 409


def test_create_user_with_short_password_returns_422(client, admin_token):
    r = client.post("/api/v1/users",
        json={"username": "user2", "password": "123", "name": "Test", "role": "student"},
        headers=auth_header(admin_token))
    assert r.status_code == 422


def test_teacher_cannot_create_user(client, teacher_token):
    r = client.post("/api/v1/users",
        json={"username": "x", "password": "pass1234", "name": "X", "role": "student"},
        headers=auth_header(teacher_token))
    assert r.status_code == 403


def test_admin_can_get_user_by_id(client, admin_token, teacher_user):
    r = client.get(f"/api/v1/users/{teacher_user.id}", headers=auth_header(admin_token))
    assert r.status_code == 200
    assert r.json()["username"] == "teacher1"


def test_get_nonexistent_user_returns_404(client, admin_token):
    assert client.get("/api/v1/users/99999", headers=auth_header(admin_token)).status_code == 404


def test_admin_can_update_user(client, admin_token, teacher_user):
    r = client.put(f"/api/v1/users/{teacher_user.id}",
        json={"name": "张老师（更新）", "is_active": True},
        headers=auth_header(admin_token))
    assert r.status_code == 200
    assert r.json()["name"] == "张老师（更新）"


def test_admin_can_deactivate_user(client, admin_token, teacher_user):
    r = client.put(f"/api/v1/users/{teacher_user.id}",
        json={"name": "张老师", "is_active": False},
        headers=auth_header(admin_token))
    assert r.status_code == 200
    assert r.json()["is_active"] is False


def test_admin_cannot_delete_themselves(client, admin_token, admin_user):
    assert client.delete(f"/api/v1/users/{admin_user.id}", headers=auth_header(admin_token)).status_code == 400


def test_admin_can_delete_other_user(client, admin_token, teacher_user):
    assert client.delete(f"/api/v1/users/{teacher_user.id}", headers=auth_header(admin_token)).status_code == 204


def test_admin_can_reset_any_user_password(client, admin_token, teacher_user):
    r = client.patch(f"/api/v1/users/{teacher_user.id}/password",
        json={"new_password": "newpass123"}, headers=auth_header(admin_token))
    assert r.status_code == 200


def test_user_can_change_own_password(client, teacher_token, teacher_user):
    r = client.patch(f"/api/v1/users/{teacher_user.id}/password",
        json={"current_password": "teach123", "new_password": "newpass456"},
        headers=auth_header(teacher_token))
    assert r.status_code == 200


def test_user_cannot_change_others_password(client, teacher_token, admin_user):
    r = client.patch(f"/api/v1/users/{admin_user.id}/password",
        json={"current_password": "teach123", "new_password": "hack123"},
        headers=auth_header(teacher_token))
    assert r.status_code == 403
