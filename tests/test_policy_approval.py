from fastapi.testclient import TestClient
from app.models.user import User


def test_complete_approval_workflow(client: TestClient, admin_user: User, government_user: User, auth_headers):
    """
    Test full lifecycle:
    DRAFT -> PENDING_APPROVAL -> APPROVED -> PUBLISHED
    """
    gov_h = auth_headers(government_user)
    admin_h = auth_headers(admin_user)

    # 1. Create policy in DRAFT
    create_resp = client.post(
        "/api/v1/policies",
        json={"title": "National Highway Expansion Policy", "category": "Infrastructure"},
        headers=gov_h,
    )
    assert create_resp.status_code == 201
    policy_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "DRAFT"

    # 2. Submit for approval -> PENDING_APPROVAL
    submit_resp = client.post(f"/api/v1/policies/{policy_id}/submit", headers=gov_h)
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "PENDING_APPROVAL"

    # 3. Approve policy -> APPROVED
    approve_resp = client.post(f"/api/v1/policies/{policy_id}/approve", headers=admin_h)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"
    assert approve_resp.json()["approved_by_id"] == admin_user.id


def test_approve_and_publish_directly(client: TestClient, admin_user: User, auth_headers):
    """Approve with publish flag transitions directly to PUBLISHED with publication date."""
    headers = auth_headers(admin_user)

    # Create & submit
    create_resp = client.post(
        "/api/v1/policies",
        json={"title": "National Water Conservation Act", "category": "Environment"},
        headers=headers,
    )
    policy_id = create_resp.json()["id"]
    client.post(f"/api/v1/policies/{policy_id}/submit", headers=headers)

    # Approve with publish=True
    approve_resp = client.post(
        f"/api/v1/policies/{policy_id}/approve",
        json={"publish": True},
        headers=headers,
    )
    assert approve_resp.status_code == 200
    data = approve_resp.json()
    assert data["status"] == "PUBLISHED"
    assert data["publication_date"] is not None


def test_rejection_workflow(client: TestClient, admin_user: User, government_user: User, auth_headers):
    """
    Test rejection lifecycle:
    PENDING_APPROVAL -> REJECTED -> submit -> PENDING_APPROVAL
    """
    gov_h = auth_headers(government_user)
    admin_h = auth_headers(admin_user)

    create_resp = client.post(
        "/api/v1/policies",
        json={"title": "Proposed Urban Housing Scheme", "category": "Housing"},
        headers=gov_h,
    )
    policy_id = create_resp.json()["id"]

    # Submit
    client.post(f"/api/v1/policies/{policy_id}/submit", headers=gov_h)

    # Reject with feedback reason
    reject_resp = client.post(
        f"/api/v1/policies/{policy_id}/reject",
        json={"reason": "Insufficient environmental impact assessment provided."},
        headers=admin_h,
    )
    assert reject_resp.status_code == 200
    data = reject_resp.json()
    assert data["status"] == "REJECTED"
    assert data["rejection_reason"] == "Insufficient environmental impact assessment provided."

    # Can be re-submitted from REJECTED
    resubmit_resp = client.post(f"/api/v1/policies/{policy_id}/submit", headers=gov_h)
    assert resubmit_resp.status_code == 200
    assert resubmit_resp.json()["status"] == "PENDING_APPROVAL"


def test_invalid_status_transitions(client: TestClient, admin_user: User, auth_headers):
    """Attempting invalid status transitions raises 400 Bad Request."""
    headers = auth_headers(admin_user)

    create_resp = client.post(
        "/api/v1/policies",
        json={"title": "Invalid Transition Policy", "category": "Finance"},
        headers=headers,
    )
    policy_id = create_resp.json()["id"]

    # Cannot approve while in DRAFT
    approve_draft = client.post(f"/api/v1/policies/{policy_id}/approve", headers=headers)
    assert approve_draft.status_code == 400
    assert "Cannot approve" in approve_draft.json()["detail"]

    # Cannot reject while in DRAFT
    reject_draft = client.post(f"/api/v1/policies/{policy_id}/reject", headers=headers)
    assert reject_draft.status_code == 400
    assert "Cannot reject" in reject_draft.json()["detail"]

    # Advance to PENDING_APPROVAL
    client.post(f"/api/v1/policies/{policy_id}/submit", headers=headers)

    # Cannot re-submit while already PENDING_APPROVAL
    double_submit = client.post(f"/api/v1/policies/{policy_id}/submit", headers=headers)
    assert double_submit.status_code == 400
    assert "Cannot submit" in double_submit.json()["detail"]


def test_unauthorized_approval_actions(client: TestClient, admin_user: User, citizen_user: User, auth_headers):
    """Citizens and guests cannot perform approval actions (403 Forbidden / 401 Unauthorized)."""
    admin_h = auth_headers(admin_user)
    citizen_h = auth_headers(citizen_user)

    create_resp = client.post(
        "/api/v1/policies",
        json={"title": "Sensitive State Policy", "category": "Digital Governance"},
        headers=admin_h,
    )
    policy_id = create_resp.json()["id"]
    client.post(f"/api/v1/policies/{policy_id}/submit", headers=admin_h)

    # Citizen tries to approve -> 403
    cit_approve = client.post(f"/api/v1/policies/{policy_id}/approve", headers=citizen_h)
    assert cit_approve.status_code == 403

    # Citizen tries to reject -> 403
    cit_reject = client.post(f"/api/v1/policies/{policy_id}/reject", headers=citizen_h)
    assert cit_reject.status_code == 403

    # Anonymous tries to approve -> 401
    anon_approve = client.post(f"/api/v1/policies/{policy_id}/approve")
    assert anon_approve.status_code == 401
