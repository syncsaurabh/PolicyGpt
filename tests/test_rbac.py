from fastapi.testclient import TestClient
from app.models.user import User


def test_admin_endpoint_as_admin_allowed(client: TestClient, admin_user: User, auth_headers):
    """Administrator can access admin endpoint."""
    headers = auth_headers(admin_user)
    response = client.get("/api/v1/users/admin/test", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Admin access granted" in data["message"]


def test_admin_endpoint_as_citizen_forbidden(client: TestClient, citizen_user: User, auth_headers):
    """Citizen accessing admin endpoint is denied (403 Forbidden)."""
    headers = auth_headers(citizen_user)
    response = client.get("/api/v1/users/admin/test", headers=headers)
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_government_endpoint_as_government_allowed(client: TestClient, government_user: User, auth_headers):
    """Government official can access government endpoint."""
    headers = auth_headers(government_user)
    response = client.get("/api/v1/users/government/test", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Government Official" in data["message"]


def test_government_endpoint_as_citizen_forbidden(client: TestClient, citizen_user: User, auth_headers):
    """Citizen accessing government endpoint is denied (403 Forbidden)."""
    headers = auth_headers(citizen_user)
    response = client.get("/api/v1/users/government/test", headers=headers)
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_unauthenticated_access_to_rbac_endpoints(client: TestClient):
    """Unauthenticated requests to RBAC endpoints return 401."""
    resp_admin = client.get("/api/v1/users/admin/test")
    assert resp_admin.status_code == 401

    resp_gov = client.get("/api/v1/users/government/test")
    assert resp_gov.status_code == 401
