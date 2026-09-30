from fastapi.testclient import TestClient
from app.models.user import User


def test_compare_two_and_three_schemes(client: TestClient, admin_user: User, auth_headers):
    """Can compare 2 and 3 schemes side-by-side with structured attributes."""
    headers = auth_headers(admin_user)

    s1 = client.post(
        "/api/v1/schemes",
        json={"name": "Comparison Scheme A", "category": "Healthcare", "department": "Health", "benefits": "Free checkups"},
        headers=headers,
    ).json()["id"]

    s2 = client.post(
        "/api/v1/schemes",
        json={"name": "Comparison Scheme B", "category": "Healthcare", "department": "AYUSH", "benefits": "Free medicine"},
        headers=headers,
    ).json()["id"]

    s3 = client.post(
        "/api/v1/schemes",
        json={"name": "Comparison Scheme C", "category": "Healthcare", "department": "Public Health", "benefits": "Diagnostic subsidy"},
        headers=headers,
    ).json()["id"]

    # 1. Compare 2 schemes
    resp_2 = client.post("/api/v1/comparison", json={"scheme_ids": [s1, s2]})
    assert resp_2.status_code == 200
    data_2 = resp_2.json()
    assert data_2["comparison_type"] == "scheme"
    assert len(data_2["items"]) == 2
    assert data_2["items"][0]["id"] == s1
    assert data_2["items"][1]["id"] == s2

    # 2. Compare 3 schemes
    resp_3 = client.post("/api/v1/comparison", json={"scheme_ids": [s1, s2, s3]})
    assert resp_3.status_code == 200
    assert len(resp_3.json()["items"]) == 3


def test_compare_policies(client: TestClient, admin_user: User, auth_headers):
    """Can compare policies side-by-side."""
    headers = auth_headers(admin_user)

    p1 = client.post(
        "/api/v1/policies",
        json={"title": "Comparison Policy 1", "category": "Education", "status": "PUBLISHED"},
        headers=headers,
    ).json()["id"]

    p2 = client.post(
        "/api/v1/policies",
        json={"title": "Comparison Policy 2", "category": "Education", "status": "PUBLISHED"},
        headers=headers,
    ).json()["id"]

    resp = client.post("/api/v1/comparison", json={"policy_ids": [p1, p2]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["comparison_type"] == "policy"
    assert len(data["items"]) == 2


def test_comparison_validation_errors(client: TestClient):
    """Validate limits on comparison items (fewer than 2, more than 3, duplicates, missing)."""
    # Fewer than 2 items -> 422
    resp_under = client.post("/api/v1/comparison", json={"scheme_ids": [1]})
    assert resp_under.status_code in (400, 422)

    # More than 3 items -> 422
    resp_over = client.post("/api/v1/comparison", json={"scheme_ids": [1, 2, 3, 4]})
    assert resp_over.status_code in (400, 422)

    # Duplicate IDs -> 422
    resp_dup = client.post("/api/v1/comparison", json={"scheme_ids": [1, 1]})
    assert resp_dup.status_code in (400, 422)

    # Non-existent ID -> 404
    resp_missing = client.post("/api/v1/comparison", json={"scheme_ids": [99991, 99992]})
    assert resp_missing.status_code == 404


def test_comparison_archived_restricted_for_citizens(
    client: TestClient,
    admin_user: User,
    citizen_user: User,
    auth_headers,
):
    """Citizen cannot compare archived/restricted schemes."""
    admin_h = auth_headers(admin_user)
    citizen_h = auth_headers(citizen_user)

    s_active = client.post(
        "/api/v1/schemes",
        json={"name": "Active Public Scheme", "category": "Housing"},
        headers=admin_h,
    ).json()["id"]

    s_archived = client.post(
        "/api/v1/schemes",
        json={"name": "Archived Scheme", "category": "Housing"},
        headers=admin_h,
    ).json()["id"]
    client.delete(f"/api/v1/schemes/{s_archived}", headers=admin_h)

    # Citizen comparison fails with 403 Forbidden
    resp = client.post(
        "/api/v1/comparison",
        json={"scheme_ids": [s_active, s_archived]},
        headers=citizen_h,
    )
    assert resp.status_code == 403
    assert "archived or restricted" in resp.json()["detail"]
