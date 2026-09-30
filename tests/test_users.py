from fastapi.testclient import TestClient
from app.models.user import User, UserRole


def test_get_me_success(client: TestClient, citizen_user: User, auth_headers):
    """Test GET /api/v1/users/me returns authenticated user's details."""
    headers = auth_headers(citizen_user)
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == citizen_user.id
    assert data["name"] == citizen_user.name
    assert data["email"] == citizen_user.email
    assert data["role"] == citizen_user.role.value
    assert "password_hash" not in data


def test_get_me_unauthorized_no_token(client: TestClient):
    """Test GET /api/v1/users/me without token returns 401."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_get_me_invalid_token(client: TestClient):
    """Test GET /api/v1/users/me with malformed token returns 401."""
    response = client.get("/api/v1/users/me", headers={"Authorization": "Bearer not-a-valid-token"})
    assert response.status_code == 401


def test_update_me_profile(client: TestClient, citizen_user: User, auth_headers):
    """Test PUT /api/v1/users/me updates allowable fields like name."""
    headers = auth_headers(citizen_user)
    response = client.put(
        "/api/v1/users/me",
        headers=headers,
        json={"name": "Jane Citizen Updated"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Citizen Updated"
    assert data["email"] == citizen_user.email


def test_update_me_ignores_protected_fields(client: TestClient, citizen_user: User, auth_headers):
    """Test PUT /api/v1/users/me does not permit changing role or email."""
    headers = auth_headers(citizen_user)
    response = client.put(
        "/api/v1/users/me",
        headers=headers,
        json={"name": "Jane Hacked", "role": "ADMINISTRATOR", "email": "hacked@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == UserRole.CITIZEN.value
    assert data["email"] == citizen_user.email
