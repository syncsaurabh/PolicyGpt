from fastapi.testclient import TestClient
from app.models.user import User


def test_create_policy_as_admin(client: TestClient, admin_user: User, auth_headers):
    """Administrator can successfully create a policy."""
    headers = auth_headers(admin_user)
    payload = {
        "title": "National Digital Literacy Mission",
        "description": "Comprehensive digital skills enablement program for rural citizens.",
        "category": "Education",
        "department": "Department of Electronics and IT",
        "ministry": "Ministry of Electronics and Information Technology",
        "state": "Central",
        "sector": "Digital Governance",
        "is_active": True,
    }
    response = client.post("/api/v1/policies", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["category"] == "Education"
    assert data["status"] == "DRAFT"
    assert data["id"] is not None


def test_create_policy_as_government_official(client: TestClient, government_user: User, auth_headers):
    """Government Official can create a policy."""
    headers = auth_headers(government_user)
    payload = {
        "title": "Clean Energy Infrastructure Plan",
        "description": "Solar subsidy and grid expansion framework.",
        "category": "Infrastructure",
        "department": "Renewable Energy Division",
    }
    response = client.post("/api/v1/policies", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["title"] == payload["title"]


def test_create_policy_as_citizen_forbidden(client: TestClient, citizen_user: User, auth_headers):
    """Citizen cannot create policies (403 Forbidden)."""
    headers = auth_headers(citizen_user)
    payload = {
        "title": "Citizen Proposed Policy",
        "description": "Attempted submission by a citizen.",
        "category": "Education",
    }
    response = client.post("/api/v1/policies", json=payload, headers=headers)
    assert response.status_code == 403


def test_create_policy_unauthenticated(client: TestClient):
    """Unauthenticated request to create policy returns 401."""
    payload = {"title": "Anonymous Policy", "category": "Finance"}
    response = client.post("/api/v1/policies", json=payload)
    assert response.status_code == 401


def test_get_policy_details(client: TestClient, admin_user: User, citizen_user: User, auth_headers):
    """Verify policy retrieval and publication status access rules."""
    admin_h = auth_headers(admin_user)
    citizen_h = auth_headers(citizen_user)

    # 1. Create a draft policy
    create_resp = client.post(
        "/api/v1/policies",
        json={"title": "Draft Health Blueprint", "category": "Healthcare", "department": "Ministry of Health"},
        headers=admin_h,
    )
    policy_id = create_resp.json()["id"]

    # Admin can view draft policy
    admin_view = client.get(f"/api/v1/policies/{policy_id}", headers=admin_h)
    assert admin_view.status_code == 200
    assert admin_view.json()["id"] == policy_id

    # Citizen cannot view draft policy (404 Not Found)
    citizen_view = client.get(f"/api/v1/policies/{policy_id}", headers=citizen_h)
    assert citizen_view.status_code == 404

    # 2. Advance to published
    client.post(f"/api/v1/policies/{policy_id}/submit", headers=admin_h)
    client.post(f"/api/v1/policies/{policy_id}/approve", json={"publish": True}, headers=admin_h)

    # Now citizen and guest can view published policy
    citizen_published_view = client.get(f"/api/v1/policies/{policy_id}", headers=citizen_h)
    assert citizen_published_view.status_code == 200
    assert citizen_published_view.json()["status"] == "PUBLISHED"

    guest_view = client.get(f"/api/v1/policies/{policy_id}")
    assert guest_view.status_code == 200


def test_update_policy(client: TestClient, admin_user: User, auth_headers):
    """Administrator can update existing policy fields."""
    headers = auth_headers(admin_user)
    create_resp = client.post(
        "/api/v1/policies",
        json={"title": "Original Policy Title", "category": "Finance"},
        headers=headers,
    )
    policy_id = create_resp.json()["id"]

    update_payload = {
        "title": "Updated Policy Title",
        "description": "Revised descriptive summary.",
        "department": "Finance Commission",
    }
    update_resp = client.put(f"/api/v1/policies/{policy_id}", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["title"] == "Updated Policy Title"
    assert data["description"] == "Revised descriptive summary."
    assert data["department"] == "Finance Commission"


def test_archive_policy(client: TestClient, admin_user: User, auth_headers):
    """Administrator can archive a policy (soft delete)."""
    headers = auth_headers(admin_user)
    create_resp = client.post(
        "/api/v1/policies",
        json={"title": "Policy to be Archived", "category": "Environment"},
        headers=headers,
    )
    policy_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/policies/{policy_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["is_active"] is False
    assert del_resp.json()["status"] == "ARCHIVED"


def test_list_policies_pagination_and_filter(client: TestClient, admin_user: User, auth_headers):
    """Policies can be listed, paginated, and filtered by category and department."""
    headers = auth_headers(admin_user)

    for i in range(5):
        client.post(
            "/api/v1/policies",
            json={
                "title": f"Agriculture Policy Series {i}",
                "category": "Agriculture",
                "department": "Department of Agriculture & Farmers Welfare",
                "state": "Maharashtra",
            },
            headers=headers,
        )

    response = client.get(
        "/api/v1/policies",
        params={"category": "Agriculture", "page": 1, "page_size": 3, "sort_by": "title", "sort_order": "asc"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] >= 5
    assert len(data["results"]) == 3
    assert data["page"] == 1
    assert data["page_size"] == 3
