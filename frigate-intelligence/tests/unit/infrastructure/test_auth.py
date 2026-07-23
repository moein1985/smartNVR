"""Regression tests for Phase 16.1 — Authentication & User Management.

Tests: test_feat_016_1_auth_login_success, test_feat_016_1_auth_login_invalid_password,
       test_feat_016_1_auth_token_verify, test_feat_016_1_auth_role_check_admin,
       test_feat_016_1_auth_role_check_user_denied, test_feat_016_1_user_crud_create,
       test_feat_016_1_user_crud_delete, test_feat_016_1_user_seed_admin_undeletable
"""

import pytest
from fastapi.testclient import TestClient

from frigate_intelligence.infrastructure.auth.auth_service import AuthService
from frigate_intelligence.infrastructure.config.user_manager import UserManager


@pytest.fixture
def temp_user_manager(tmp_path):
    """Create a UserManager with a temp file path."""
    return UserManager(file_path=str(tmp_path / "users.json"))


@pytest.fixture
def auth_service():
    return AuthService()


# ─── AuthService tests ───


def test_feat_016_1_auth_password_hashing(auth_service):
    """Password hashing and verification works correctly."""
    hashed = auth_service.hash_password("mypassword")
    assert hashed != "mypassword"
    assert auth_service.verify_password("mypassword", hashed) is True
    assert auth_service.verify_password("wrongpassword", hashed) is False


def test_feat_016_1_auth_token_verify(auth_service):
    """Token creation and verification works."""
    token = auth_service.create_token("user123", "testuser", "admin")
    payload = auth_service.decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user123"
    assert payload["username"] == "testuser"
    assert payload["role"] == "admin"


def test_feat_016_1_auth_token_invalid(auth_service):
    """Invalid token returns None."""
    payload = auth_service.decode_token("invalid.token.here")
    assert payload is None


# ─── UserManager tests ───


def test_feat_016_1_user_seed_admin_undeletable(temp_user_manager):
    """Seed admin user cannot be deleted."""
    users = temp_user_manager.list_users()
    assert len(users) == 2

    admin = temp_user_manager.get_by_username("admin")
    assert admin is not None
    assert admin.role == "admin"
    assert admin.is_seed is True

    with pytest.raises(ValueError, match="Seed users cannot be deleted"):
        temp_user_manager.delete_user(admin.id)


def test_feat_016_1_user_seed_user_undeletable(temp_user_manager):
    """Seed user account cannot be deleted."""
    user = temp_user_manager.get_by_username("user")
    assert user is not None
    assert user.role == "user"
    assert user.is_seed is True

    with pytest.raises(ValueError, match="Seed users cannot be deleted"):
        temp_user_manager.delete_user(user.id)


def test_feat_016_1_user_crud_create(temp_user_manager):
    """Creating a new user works."""
    new_user = temp_user_manager.create_user("alice", "alicepass", "admin")
    assert new_user.username == "alice"
    assert new_user.role == "admin"
    assert new_user.is_seed is False

    fetched = temp_user_manager.get_by_username("alice")
    assert fetched is not None
    assert fetched.id == new_user.id


def test_feat_016_1_user_crud_create_duplicate(temp_user_manager):
    """Creating a duplicate username raises ValueError."""
    with pytest.raises(ValueError, match="already exists"):
        temp_user_manager.create_user("admin", "whatever", "user")


def test_feat_016_1_user_crud_delete(temp_user_manager):
    """Deleting a non-seed user works."""
    new_user = temp_user_manager.create_user("bob", "bobpass", "user")
    result = temp_user_manager.delete_user(new_user.id)
    assert result is True
    assert temp_user_manager.get_by_username("bob") is None


def test_feat_016_1_user_crud_update(temp_user_manager):
    """Updating user password and role works."""
    new_user = temp_user_manager.create_user("carol", "carolpass", "user")
    updated = temp_user_manager.update_user(new_user.id, password="newpass", role="admin")
    assert updated.role == "admin"

    auth = AuthService()
    assert auth.verify_password("newpass", updated.password_hash) is True
    assert auth.verify_password("carolpass", updated.password_hash) is False


def test_feat_016_1_user_crud_invalid_role(temp_user_manager):
    """Creating user with invalid role raises ValueError."""
    with pytest.raises(ValueError, match="Invalid role"):
        temp_user_manager.create_user("dave", "davepass", "superadmin")


# ─── Auth API endpoint tests (via FastAPI TestClient) ───


@pytest.fixture
def auth_app(tmp_path):
    """Create a FastAPI app with auth routes for testing."""
    from fastapi import FastAPI
    from frigate_intelligence.infrastructure.api.routes.auth_routes import (
        _get_user_manager,
        create_auth_router,
        create_user_router,
    )

    app = FastAPI()
    app.include_router(create_auth_router())
    app.include_router(create_user_router())

    _temp_manager = UserManager(file_path=str(tmp_path / "users.json"))
    app.dependency_overrides[_get_user_manager] = lambda: _temp_manager
    return app


@pytest.fixture
def auth_client(auth_app):
    return TestClient(auth_app)


def test_feat_016_1_auth_login_success(auth_client):
    """Login with correct admin credentials returns token."""
    response = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["username"] == "admin"
    assert data["role"] == "admin"


def test_feat_016_1_auth_login_invalid_password(auth_client):
    """Login with wrong password returns 401."""
    response = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_feat_016_1_auth_login_nonexistent_user(auth_client):
    """Login with non-existent user returns 401."""
    response = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "ghost", "password": "whatever"},
    )
    assert response.status_code == 401


def test_feat_016_1_auth_me_with_token(auth_client):
    """GET /me with valid token returns user info."""
    login_resp = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    token = login_resp.json()["token"]

    response = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


def test_feat_016_1_auth_me_without_token(auth_client):
    """GET /me without token returns 401."""
    response = auth_client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_feat_016_1_auth_role_check_admin(auth_client):
    """Admin user can access user management endpoints."""
    login_resp = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    token = login_resp.json()["token"]

    response = auth_client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 2


def test_feat_016_1_auth_role_check_user_denied(auth_client):
    """Regular user cannot access user management endpoints."""
    login_resp = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "user", "password": "user"},
    )
    token = login_resp.json()["token"]

    response = auth_client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_feat_016_1_auth_user_create_via_api(auth_client):
    """Admin can create a new user via API."""
    login_resp = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    token = login_resp.json()["token"]

    response = auth_client.post(
        "/api/v1/users",
        json={"username": "newuser", "password": "newpass", "role": "user"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["role"] == "user"


def test_feat_016_1_auth_user_delete_seed_via_api(auth_client):
    """Deleting seed admin via API returns 400."""
    login_resp = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    token = login_resp.json()["token"]

    me_resp = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    admin_id = me_resp.json()["id"]

    response = auth_client.delete(
        f"/api/v1/users/{admin_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
