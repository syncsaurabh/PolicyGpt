from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import create_password_reset_token, verify_password
from app.models.user import User, UserRole


def test_user_registration_success(client: TestClient, db_session: Session):
    """Test user registration with valid details."""
    payload = {
        "name": "New User",
        "email": "newuser@example.com",
        "password": "SecurePassword123!",
        "role": "CITIZEN"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New User"
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "CITIZEN"
    assert data["is_active"] is True
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data

    # Verify in DB that password is hashed
    db_user = db_session.query(User).filter(User.email == "newuser@example.com").first()
    assert db_user is not None
    assert db_user.password_hash != "SecurePassword123!"
    assert verify_password("SecurePassword123!", db_user.password_hash)


def test_registration_duplicate_email(client: TestClient, citizen_user: User):
    """Test registration fails with duplicate email (400)."""
    payload = {
        "name": "Duplicate Person",
        "email": citizen_user.email,
        "password": "Password123!",
        "role": "CITIZEN"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_registration_validation_short_password(client: TestClient):
    """Test registration rejects weak password (< 8 chars)."""
    payload = {
        "name": "Weak Pass User",
        "email": "weak@example.com",
        "password": "123",
        "role": "CITIZEN"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_login_success_json(client: TestClient, citizen_user: User):
    """Test login with JSON payload returns valid JWT."""
    payload = {
        "email": citizen_user.email,
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == citizen_user.email
    assert data["user"]["role"] == citizen_user.role.value


def test_login_success_form(client: TestClient, citizen_user: User):
    """Test login with form-data (OAuth2 compatible) returns valid JWT."""
    form_data = {
        "username": citizen_user.email,
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/login", data=form_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client: TestClient, citizen_user: User):
    """Test login with incorrect password returns 401."""
    payload = {
        "email": citizen_user.email,
        "password": "WrongPassword!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    """Test login with nonexistent email returns 401."""
    payload = {
        "email": "ghost@example.com",
        "password": "SomePassword123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_password_reset_flow(client: TestClient, citizen_user: User):
    """Test forgot-password and reset-password end-to-end flow."""
    # 1. Request forgot password
    forgot_resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": citizen_user.email}
    )
    assert forgot_resp.status_code == 200
    msg = forgot_resp.json()["message"]
    assert "Dev token: " in msg
    token = msg.split("Dev token: ")[1].rstrip(")")

    # 2. Reset password using token
    new_password = "BrandNewPassword999!"
    reset_resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": new_password}
    )
    assert reset_resp.status_code == 200

    # 3. Log in with new password
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": citizen_user.email, "password": new_password}
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # 4. Verify old password no longer works
    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": citizen_user.email, "password": "Password123!"}
    )
    assert old_login.status_code == 401


def test_reset_password_invalid_token(client: TestClient):
    """Test reset-password fails with invalid token."""
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid-token-12345", "new_password": "NewPassword123!"}
    )
    assert response.status_code == 400
    assert "Invalid, expired, or unrecognized password reset token" in response.json()["detail"]


def test_reset_password_expired_token(client: TestClient, citizen_user: User):
    """Test reset-password rejects expired reset token with 400."""
    expired_token = create_password_reset_token(
        email=citizen_user.email,
        expires_delta=timedelta(minutes=-10)
    )
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": expired_token, "new_password": "ExpiredPass123!"}
    )
    assert response.status_code == 400
    assert "Invalid, expired, or unrecognized password reset token" in response.json()["detail"]


def test_reset_password_with_login_access_token_rejected(client: TestClient, citizen_user: User):
    """Test passing an access token from login to reset-password is appropriately rejected with 400."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": citizen_user.email, "password": "Password123!"}
    )
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    reset_resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": access_token, "new_password": "HackedPassword123!"}
    )
    assert reset_resp.status_code == 400
    assert "access token" in reset_resp.json()["detail"].lower()


def test_forgot_password_nonexistent_email_silent(client: TestClient):
    """Test forgot-password with nonexistent email returns 200 without exposing reset token."""
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent_user@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "password reset instructions have been sent" in data["message"]
    assert data.get("reset_token") is None
    assert "Dev token:" not in data["message"]



def test_openapi_security_schemes_uses_http_bearer(client: TestClient):
    """Verify OpenAPI uses HTTPBearer and completely excludes OAuth2PasswordBearer."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    components = schema.get("components", {})
    security_schemes = components.get("securitySchemes", {})

    # Ensure HTTPBearer is configured
    assert "HTTPBearer" in security_schemes
    bearer_spec = security_schemes["HTTPBearer"]
    assert bearer_spec["type"] == "http"
    assert bearer_spec["scheme"] == "bearer"

    # Ensure OAuth2PasswordBearer and password flows are NOT present
    assert "OAuth2PasswordBearer" not in security_schemes

    # Ensure no security scheme requires client_id or client_secret
    for scheme_name, scheme_data in security_schemes.items():
        assert scheme_data.get("type") != "oauth2"
        assert "flows" not in scheme_data


def test_openapi_protected_routes_require_http_bearer(client: TestClient):
    """Verify protected endpoints require HTTPBearer security in OpenAPI."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema.get("paths", {})

    me_get_security = paths.get("/api/v1/users/me", {}).get("get", {}).get("security", [])
    assert any("HTTPBearer" in s for s in me_get_security)
    assert not any("OAuth2PasswordBearer" in s for s in me_get_security)

