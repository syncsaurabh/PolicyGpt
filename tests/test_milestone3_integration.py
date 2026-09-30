from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User


def test_complete_milestone3_policy_notification_flow(
    client: TestClient,
    admin_user: User,
    citizen_user: User,
    auth_headers,
):
    """
    Test End-to-End Flow 1:
    1. Admin creates a policy in DRAFT status
    2. Admin submits for approval (PENDING_APPROVAL)
    3. Admin approves and publishes policy (PUBLISHED)
    4. Notification system broadcasts alert to citizen
    5. Citizen fetches notification and marks as read
    6. Analytics reflect the new published policy
    """
    adm_headers = auth_headers(admin_user)
    cit_headers = auth_headers(citizen_user)

    # 1. Create Policy
    create_resp = client.post(
        "/api/v1/policies",
        json={
            "title": "National Solar Energy Policy 2026",
            "description": "Comprehensive renewable energy initiative across states.",
            "category": "Environment",
            "department": "Ministry of New and Renewable Energy",
            "status": "DRAFT",
        },
        headers=adm_headers,
    )
    assert create_resp.status_code == 201
    policy_id = create_resp.json()["id"]

    # 2. Submit for Approval
    sub_resp = client.post(f"/api/v1/policies/{policy_id}/submit", headers=adm_headers)
    assert sub_resp.status_code == 200
    assert sub_resp.json()["status"] == "PENDING_APPROVAL"

    # 3. Approve and Publish
    app_resp = client.post(
        f"/api/v1/policies/{policy_id}/approve",
        json={"publish": True},
        headers=adm_headers,
    )
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "PUBLISHED"

    # 4. Citizen retrieves in-app notifications
    notif_resp = client.get("/api/v1/notifications", headers=cit_headers)
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()["results"]
    policy_notifs = [n for n in notifs if "National Solar Energy Policy 2026" in n["title"]]
    assert len(policy_notifs) >= 1

    # 5. Citizen marks notification as read
    target_notif = policy_notifs[0]
    read_resp = client.put(f"/api/v1/notifications/{target_notif['id']}/read", headers=cit_headers)
    assert read_resp.status_code == 200
    assert read_resp.json()["is_read"] is True

    # 6. Analytics verification
    an_resp = client.get("/api/v1/analytics/policies?department=Renewable", headers=adm_headers)
    assert an_resp.status_code == 200
    assert an_resp.json()["published_count"] >= 1


def test_complete_milestone3_feedback_resolution_flow(
    client: TestClient,
    citizen_user: User,
    admin_user: User,
    auth_headers,
):
    """
    Test End-to-End Flow 2:
    1. Citizen submits a support query / issue
    2. Admin views in feedback dashboard
    3. Admin provides official resolution response
    4. Citizen receives in-app resolution notification
    5. Citizen views updated feedback details
    """
    cit_headers = auth_headers(citizen_user)
    adm_headers = auth_headers(admin_user)

    # 1. Citizen submits feedback
    fb_resp = client.post(
        "/api/v1/feedback",
        json={
            "subject": "Inquiry on Solar Subsidy Process",
            "content": "How do residential applicants upload rooftop photos?",
            "feedback_type": "INQUIRY",
            "category": "Scheme Application",
            "priority": "HIGH",
        },
        headers=cit_headers,
    )
    assert fb_resp.status_code == 201
    feedback_id = fb_resp.json()["id"]

    # 2. Admin retrieves feedback list
    list_resp = client.get("/api/v1/feedback?category=Scheme", headers=adm_headers)
    assert list_resp.status_code == 200
    assert any(f["id"] == feedback_id for f in list_resp.json()["results"])

    # 3. Admin resolves query
    res_resp = client.post(
        f"/api/v1/feedback/{feedback_id}/resolve",
        json={
            "admin_response": "You can upload JPEG/PNG photos up to 5MB in the Document Upload tab.",
            "status": "RESOLVED",
        },
        headers=adm_headers,
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "RESOLVED"

    # 4. Citizen checks notifications
    notif_resp = client.get("/api/v1/notifications", headers=cit_headers)
    assert notif_resp.status_code == 200
    assert any("Query Resolved" in n["title"] for n in notif_resp.json()["results"])

    # 5. Citizen views resolved ticket
    cit_view = client.get(f"/api/v1/feedback/{feedback_id}", headers=cit_headers)
    assert cit_view.status_code == 200
    assert cit_view.json()["status"] == "RESOLVED"
    assert "Document Upload" in cit_view.json()["admin_response"]
