import json
from fastapi.testclient import TestClient
from app.models.user import User


def test_create_scheme_with_eligibility_rules(client: TestClient, admin_user: User, auth_headers):
    """Administrator can register a scheme with initial eligibility rules."""
    headers = auth_headers(admin_user)
    payload = {
        "name": "Pradhan Mantri Kisan Samman Nidhi",
        "description": "Income support of ₹6,000 per year in three equal installments to small and marginal farmers.",
        "benefits": "Financial benefit of ₹6,000 per year directly into bank accounts.",
        "category": "Farmer Welfare",
        "department": "Department of Agriculture",
        "ministry": "Ministry of Agriculture and Farmers Welfare",
        "state": "All India",
        "sector": "Agriculture",
        "application_process": "Register online on pmkisan.gov.in or through CSC.",
        "status": "ACTIVE",
        "eligibility_rules": [
            {
                "rule_name": "Farmer Landholding & Occupation Rule",
                "criteria_json": json.dumps({"occupation": ["farmer"], "max_income": 500000}),
                "description": "Applicant must be an operational landholding farmer.",
            }
        ],
    }
    response = client.post("/api/v1/schemes", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["category"] == "Farmer Welfare"
    scheme_id = data["id"]

    # Verify retrieval with rules
    get_resp = client.get(f"/api/v1/schemes/{scheme_id}", headers=headers)
    assert get_resp.status_code == 200
    details = get_resp.json()
    assert len(details["eligibility_rules"]) == 1
    assert details["eligibility_rules"][0]["rule_name"] == "Farmer Landholding & Occupation Rule"


def test_create_scheme_invalid_policy_id(client: TestClient, admin_user: User, auth_headers):
    """Providing a non-existent parent policy_id returns 404."""
    headers = auth_headers(admin_user)
    payload = {
        "name": "Invalid Parent Scheme",
        "category": "Healthcare",
        "policy_id": 99999,
    }
    response = client.post("/api/v1/schemes", json=payload, headers=headers)
    assert response.status_code == 404
    assert "Parent Policy with ID 99999 does not exist" in response.json()["detail"]


def test_add_eligibility_rule_to_existing_scheme(client: TestClient, admin_user: User, auth_headers):
    """Rules can be dynamically appended to an existing scheme."""
    headers = auth_headers(admin_user)
    create_resp = client.post(
        "/api/v1/schemes",
        json={"name": "Post-Matric Scholarship Scheme", "category": "Scholarships"},
        headers=headers,
    )
    scheme_id = create_resp.json()["id"]

    rule_payload = {
        "rule_name": "Academic & Income Criteria",
        "criteria_json": json.dumps({"min_age": 18, "max_age": 30, "max_income": 250000, "occupation": ["student"]}),
        "description": "Eligible for students between 18-30 with family income <= 2.5L",
    }
    rule_resp = client.post(f"/api/v1/schemes/{scheme_id}/rules", json=rule_payload, headers=headers)
    assert rule_resp.status_code == 201
    rule_data = rule_resp.json()
    assert rule_data["rule_name"] == "Academic & Income Criteria"
    assert rule_data["scheme_id"] == scheme_id


def test_update_scheme(client: TestClient, admin_user: User, auth_headers):
    """Administrator can update scheme properties."""
    headers = auth_headers(admin_user)
    create_resp = client.post(
        "/api/v1/schemes",
        json={"name": "Old Scheme Name", "category": "Housing"},
        headers=headers,
    )
    scheme_id = create_resp.json()["id"]

    update_payload = {
        "name": "Updated Scheme Name",
        "benefits": "Subsidized loan interest rates for first-time home buyers.",
        "state": "Maharashtra",
    }
    update_resp = client.put(f"/api/v1/schemes/{scheme_id}", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["name"] == "Updated Scheme Name"
    assert data["state"] == "Maharashtra"


def test_archive_scheme(client: TestClient, admin_user: User, auth_headers):
    """Administrator can soft-archive a scheme."""
    headers = auth_headers(admin_user)
    create_resp = client.post(
        "/api/v1/schemes",
        json={"name": "Scheme to Archive", "category": "Social Security"},
        headers=headers,
    )
    scheme_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/schemes/{scheme_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["is_active"] is False
    assert del_resp.json()["status"] == "ARCHIVED"


def test_list_schemes_filtering_and_pagination(client: TestClient, admin_user: User, auth_headers):
    """Schemes list supports category, department, and pagination filters."""
    headers = auth_headers(admin_user)

    for i in range(4):
        client.post(
            "/api/v1/schemes",
            json={
                "name": f"Student Fellowship Scheme {i}",
                "category": "Student Schemes",
                "department": "Higher Education",
            },
            headers=headers,
        )

    response = client.get(
        "/api/v1/schemes",
        params={"category": "Student Schemes", "page": 1, "page_size": 2},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] >= 4
    assert len(data["results"]) == 2
