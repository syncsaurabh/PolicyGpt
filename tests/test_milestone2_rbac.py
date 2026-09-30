from fastapi.testclient import TestClient
from app.models.user import User


def test_rbac_roles_create_policy_permissions(
    client: TestClient,
    admin_user: User,
    government_user: User,
    citizen_user: User,
    researcher_user: User,
    organization_user: User,
    guest_user: User,
    auth_headers,
):
    """
    Verify RBAC across all 6 roles for Policy creation:
    Allowed: Administrator, Government Official
    Forbidden: Citizen, Researcher, Organization, Guest User
    Unauthorized: Unauthenticated
    """
    payload = {"title": "RBAC Verification Policy", "category": "Finance"}

    # Administrator -> 201
    resp_admin = client.post("/api/v1/policies", json=payload, headers=auth_headers(admin_user))
    assert resp_admin.status_code == 201

    # Government Official -> 201
    resp_gov = client.post("/api/v1/policies", json=payload, headers=auth_headers(government_user))
    assert resp_gov.status_code == 201

    # Citizen -> 403
    resp_cit = client.post("/api/v1/policies", json=payload, headers=auth_headers(citizen_user))
    assert resp_cit.status_code == 403

    # Researcher -> 403
    resp_res = client.post("/api/v1/policies", json=payload, headers=auth_headers(researcher_user))
    assert resp_res.status_code == 403

    # Organization -> 403
    resp_org = client.post("/api/v1/policies", json=payload, headers=auth_headers(organization_user))
    assert resp_org.status_code == 403

    # Guest User -> 403
    resp_guest = client.post("/api/v1/policies", json=payload, headers=auth_headers(guest_user))
    assert resp_guest.status_code == 403

    # Unauthenticated -> 401
    resp_anon = client.post("/api/v1/policies", json=payload)
    assert resp_anon.status_code == 401


def test_rbac_roles_create_scheme_permissions(
    client: TestClient,
    admin_user: User,
    citizen_user: User,
    researcher_user: User,
    auth_headers,
):
    """Verify RBAC on Scheme creation."""
    payload = {"name": "RBAC Scheme Verification", "category": "Scholarships"}

    # Admin -> 201
    assert client.post("/api/v1/schemes", json=payload, headers=auth_headers(admin_user)).status_code == 201

    # Citizen -> 403
    assert client.post("/api/v1/schemes", json=payload, headers=auth_headers(citizen_user)).status_code == 403

    # Researcher -> 403
    assert client.post("/api/v1/schemes", json=payload, headers=auth_headers(researcher_user)).status_code == 403

    # Unauthenticated -> 401
    assert client.post("/api/v1/schemes", json=payload).status_code == 401


def test_public_access_search_eligibility_comparison(
    client: TestClient,
    admin_user: User,
    citizen_user: User,
    guest_user: User,
    auth_headers,
):
    """
    Public features (Search, Eligibility, Comparison) accessible by Citizen, Guest, and Anonymous:
    - GET /api/v1/search/policies
    - GET /api/v1/search/schemes
    - POST /api/v1/eligibility/check
    - POST /api/v1/comparison
    """
    # 1. Anonymous search
    assert client.get("/api/v1/search/policies").status_code == 200
    assert client.get("/api/v1/search/schemes").status_code == 200

    # 2. Guest user search
    assert client.get("/api/v1/search/policies", headers=auth_headers(guest_user)).status_code == 200

    # 3. Anonymous eligibility check
    eligibility_resp = client.post("/api/v1/eligibility/check", json={"age": 25, "income": 200000})
    assert eligibility_resp.status_code == 200

    # 4. Citizen eligibility check
    citizen_eligibility = client.post(
        "/api/v1/eligibility/check",
        json={"age": 25, "income": 200000},
        headers=auth_headers(citizen_user),
    )
    assert citizen_eligibility.status_code == 200
