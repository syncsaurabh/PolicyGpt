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
    """Test PUT /api/v1/users/me updates allowable fields like name and phone_number."""
    headers = auth_headers(citizen_user)
    response = client.put(
        "/api/v1/users/me",
        headers=headers,
        json={"name": "Jane Citizen Updated", "phone_number": "+919876543210"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Citizen Updated"
    assert data["email"] == citizen_user.email
    assert data["phone_number"] == "+919876543210"


def test_update_me_partial_update_phone_only(client: TestClient, citizen_user: User, auth_headers):
    """Test PUT /api/v1/users/me updating phone only preserves existing name."""
    headers = auth_headers(citizen_user)
    # First set name
    client.put("/api/v1/users/me", headers=headers, json={"name": "Original Name"})
    # Update phone only
    response = client.put(
        "/api/v1/users/me",
        headers=headers,
        json={"phone_number": "+1234567890"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Original Name"
    assert data["phone_number"] == "+1234567890"


def test_update_me_partial_update_name_only(client: TestClient, citizen_user: User, auth_headers):
    """Test PUT /api/v1/users/me updating name only preserves existing phone."""
    headers = auth_headers(citizen_user)
    # First set phone
    client.put("/api/v1/users/me", headers=headers, json={"phone_number": "+1234567890"})
    # Update name only
    response = client.put(
        "/api/v1/users/me",
        headers=headers,
        json={"name": "New Person Name"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Person Name"
    assert data["phone_number"] == "+1234567890"


def test_update_me_ignores_protected_fields(client: TestClient, citizen_user: User, auth_headers):
    """Test PUT /api/v1/users/me does not permit changing role, email, id, or password."""
    headers = auth_headers(citizen_user)
    original_id = citizen_user.id
    original_role = citizen_user.role.value
    original_email = citizen_user.email

    response = client.put(
        "/api/v1/users/me",
        headers=headers,
        json={
            "id": 99999,
            "name": "Jane Hacked",
            "role": "ADMINISTRATOR",
            "email": "hacked@example.com",
            "password": "NewHackedPassword123!",
            "password_hash": "some_hash",
            "is_active": False,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == original_id
    assert data["name"] == "Jane Hacked"
    assert data["role"] == original_role
    assert data["email"] == original_email
    assert data["is_active"] is True
    assert "password" not in data
    assert "password_hash" not in data


def test_update_me_validation_error_short_name(client: TestClient, citizen_user: User, auth_headers):
    """Test PUT /api/v1/users/me rejects name with fewer than 2 characters."""
    headers = auth_headers(citizen_user)
    response = client.put(
        "/api/v1/users/me",
        headers=headers,
        json={"name": "A"}
    )
    assert response.status_code == 422


def test_update_me_validation_error_long_phone(client: TestClient, citizen_user: User, auth_headers):
    """Test PUT /api/v1/users/me rejects phone number longer than 50 characters."""
    headers = auth_headers(citizen_user)
    response = client.put(
        "/api/v1/users/me",
        headers=headers,
        json={"phone_number": "1" * 51}
    )
    assert response.status_code == 422


def test_update_me_profile_all_fields(client: TestClient, citizen_user: User, auth_headers):
    """Test PUT /api/v1/users/me updates name, phone_number, age, state, address, and pincode."""
    headers = auth_headers(citizen_user)
    response = client.put(
        "/api/v1/users/me",
        headers=headers,
        json={
            "name": "Jane Citizen Complete",
            "phone_number": "+919876543210",
            "age": 29,
            "state": "Maharashtra",
            "address": "123 FC Road, Pune",
            "pincode": "411004"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Citizen Complete"
    assert data["phone_number"] == "+919876543210"
    assert data["age"] == 29
    assert data["state"] == "Maharashtra"
    assert data["address"] == "123 FC Road, Pune"
    assert data["pincode"] == "411004"


def test_update_me_validation_error_invalid_age(client: TestClient, citizen_user: User, auth_headers):
    """Test PUT /api/v1/users/me rejects invalid age (<1 or >120)."""
    headers = auth_headers(citizen_user)
    response_low = client.put(
        "/api/v1/users/me",
        headers=headers,
        json={"age": 0}
    )
    assert response_low.status_code == 422

    response_high = client.put(
        "/api/v1/users/me",
        headers=headers,
        json={"age": 150}
    )
    assert response_high.status_code == 422


def test_update_me_unauthorized(client: TestClient):
    """Test PUT /api/v1/users/me without token returns 401."""
    response = client.put("/api/v1/users/me", json={"name": "Anonymous"})
    assert response.status_code == 401
