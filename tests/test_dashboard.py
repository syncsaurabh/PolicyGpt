import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.application import SchemeApplication
from app.models.audit_log import AuditLog
from app.models.notification import Notification, NotificationType
from app.models.policy import Policy, PolicyStatus
from app.models.saved_policy import SavedPolicy
from app.models.scheme import Scheme, SchemeStatus
from app.models.search_history import SearchHistory
from app.models.user import User, UserRole


def test_unauthenticated_dashboard_endpoints(client: TestClient):
    """Verify that unauthenticated requests to all dashboard endpoints return 401."""
    resp_citizen = client.get("/api/v1/dashboard/citizen")
    assert resp_citizen.status_code == 401

    resp_gov = client.get("/api/v1/dashboard/government")
    assert resp_gov.status_code == 401

    resp_admin = client.get("/api/v1/dashboard/admin")
    assert resp_admin.status_code == 401


def test_citizen_dashboard_success(
    client: TestClient,
    db_session: Session,
    citizen_user: User,
    auth_headers,
):
    """Verify that a Citizen user can retrieve their comprehensive aggregated dashboard."""
    # 1. Create a Policy and save it
    policy = Policy(
        title="National Solar Subsidy Policy",
        category="Environment",
        department="Ministry of New and Renewable Energy",
        status=PolicyStatus.PUBLISHED.value,
        is_active=True,
    )
    db_session.add(policy)
    db_session.commit()
    db_session.refresh(policy)

    saved_policy = SavedPolicy(
        user_id=citizen_user.id,
        policy_id=policy.id,
        notes="Important for rooftop solar",
    )
    db_session.add(saved_policy)

    # 2. Create an active Scheme
    scheme = Scheme(
        name="PM Surya Ghar Yojana",
        category="Environment",
        department="Ministry of New and Renewable Energy",
        status=SchemeStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(scheme)
    db_session.commit()
    db_session.refresh(scheme)

    # 3. Create a Notification for this citizen
    notification = Notification(
        user_id=citizen_user.id,
        title="Application Received",
        message="Your application is under initial verification",
        notification_type=NotificationType.APPLICATION_UPDATE.value,
        is_read=False,
    )
    db_session.add(notification)

    # 4. Record a SearchHistory entry for this citizen
    search_entry = SearchHistory(
        user_id=citizen_user.id,
        query="solar subsidy",
        filters_json=json.dumps({"type": "scheme"}),
        result_count=1,
    )
    db_session.add(search_entry)

    # 5. Record a SchemeApplication for this citizen
    application = SchemeApplication(
        user_id=citizen_user.id,
        scheme_id=scheme.id,
        application_number="APP-202609-SOLAR01",
        status="SUBMITTED",
        remarks="Submitted with electricity bill copy",
    )
    db_session.add(application)
    db_session.commit()

    headers = auth_headers(citizen_user)
    response = client.get("/api/v1/dashboard/citizen", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "saved_policies" in data
    assert "eligible_schemes" in data
    assert "recent_notifications" in data
    assert "search_history" in data
    assert "application_status" in data

    # Verify contents
    assert len(data["saved_policies"]) >= 1
    assert data["saved_policies"][0]["policy_id"] == policy.id
    assert data["saved_policies"][0]["title"] == "National Solar Subsidy Policy"

    assert len(data["recent_notifications"]) >= 1
    assert data["recent_notifications"][0]["title"] == "Application Received"

    assert len(data["search_history"]) >= 1
    assert data["search_history"][0]["query"] == "solar subsidy"

    assert len(data["application_status"]) >= 1
    assert data["application_status"][0]["scheme_id"] == scheme.id
    assert data["application_status"][0]["status"] == "SUBMITTED"


def test_citizen_dashboard_isolation(
    client: TestClient,
    db_session: Session,
    citizen_user: User,
    auth_headers,
):
    """Verify that Citizen A only receives their own data and cannot see Citizen B's data."""
    # Create Citizen B
    citizen_b = User(
        name="Citizen Bob",
        email="bob_citizen@example.com",
        password_hash=get_password_hash("BobSecret123!"),
        role=UserRole.CITIZEN,
        is_active=True,
    )
    db_session.add(citizen_b)
    db_session.commit()
    db_session.refresh(citizen_b)

    # Create private data for Citizen B
    p_b = Policy(title="Bob's Private Crop Policy", status=PolicyStatus.PUBLISHED.value)
    db_session.add(p_b)
    db_session.commit()
    db_session.refresh(p_b)

    s_b = Scheme(name="Bob's Private Agri Scheme", status=SchemeStatus.ACTIVE.value)
    db_session.add(s_b)
    db_session.commit()
    db_session.refresh(s_b)

    saved_b = SavedPolicy(user_id=citizen_b.id, policy_id=p_b.id, notes="Bob's note")
    notif_b = Notification(user_id=citizen_b.id, title="Bob's Alert", message="Secret message")
    search_b = SearchHistory(user_id=citizen_b.id, query="bob specific search", result_count=5)
    app_b = SchemeApplication(
        user_id=citizen_b.id,
        scheme_id=s_b.id,
        application_number="APP-BOB-999",
        status="UNDER_REVIEW",
    )
    db_session.add_all([saved_b, notif_b, search_b, app_b])
    db_session.commit()

    # Query Citizen A's dashboard
    headers_a = auth_headers(citizen_user)
    resp = client.get("/api/v1/dashboard/citizen", headers=headers_a)
    assert resp.status_code == 200
    data = resp.json()

    # Check that Citizen B's items are NOT present in Citizen A's dashboard
    saved_policy_ids = [sp["policy_id"] for sp in data["saved_policies"]]
    assert p_b.id not in saved_policy_ids

    notif_titles = [n["title"] for n in data["recent_notifications"]]
    assert "Bob's Alert" not in notif_titles

    search_queries = [s["query"] for s in data["search_history"]]
    assert "bob specific search" not in search_queries

    app_numbers = [a["application_number"] for a in data["application_status"]]
    assert "APP-BOB-999" not in app_numbers


def test_citizen_cannot_access_privileged_dashboards(
    client: TestClient,
    citizen_user: User,
    auth_headers,
):
    """Verify that a Citizen cannot access Government or Admin dashboards (403)."""
    headers = auth_headers(citizen_user)

    resp_gov = client.get("/api/v1/dashboard/government", headers=headers)
    assert resp_gov.status_code == 403

    resp_admin = client.get("/api/v1/dashboard/admin", headers=headers)
    assert resp_admin.status_code == 403


def test_government_dashboard_success(
    client: TestClient,
    db_session: Session,
    government_user: User,
    auth_headers,
):
    """Verify that a Government Official can retrieve their operational dashboard."""
    # Seed a policy and scheme under Agriculture
    policy = Policy(
        title="Pradhan Mantri Fasal Bima Yojana",
        category="Agriculture",
        department="Ministry of Agriculture",
        status=PolicyStatus.PUBLISHED.value,
        is_active=True,
    )
    scheme = Scheme(
        name="Crop Insurance Scheme",
        category="Agriculture",
        department="Ministry of Agriculture",
        status=SchemeStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add_all([policy, scheme])
    db_session.commit()

    headers = auth_headers(government_user)
    resp = client.get("/api/v1/dashboard/government", headers=headers)
    assert resp.status_code == 200

    data = resp.json()
    assert "policy_statistics" in data
    assert "scheme_usage" in data
    assert "user_activity" in data
    assert "department_reports" in data
    assert "notification_statistics" in data

    assert data["policy_statistics"]["total_policies"] >= 1
    assert data["scheme_usage"]["total_schemes"] >= 1
    assert isinstance(data["department_reports"], list)


def test_government_cannot_access_admin_or_citizen_dashboard(
    client: TestClient,
    government_user: User,
    auth_headers,
):
    """Verify that a Government Official cannot access Admin or Citizen dashboards."""
    headers = auth_headers(government_user)

    resp_admin = client.get("/api/v1/dashboard/admin", headers=headers)
    assert resp_admin.status_code == 403

    resp_citizen = client.get("/api/v1/dashboard/citizen", headers=headers)
    assert resp_citizen.status_code == 403


def test_admin_dashboard_success(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    auth_headers,
):
    """Verify that an Administrator can retrieve full governance dashboard."""
    # Seed audit log
    audit = AuditLog(
        user_id=admin_user.id,
        action="TEST_ADMIN_ACTION",
        entity_type="SYSTEM",
        details="Administrative compliance check",
    )
    db_session.add(audit)
    db_session.commit()

    headers = auth_headers(admin_user)
    resp = client.get("/api/v1/dashboard/admin", headers=headers)
    assert resp.status_code == 200

    data = resp.json()
    assert "user_management" in data
    assert "policy_management" in data
    assert "analytics" in data
    assert "reports" in data
    assert "audit_logs" in data

    assert data["user_management"]["total_users"] >= 1
    assert len(data["audit_logs"]) >= 1
    assert any(log["action"] == "TEST_ADMIN_ACTION" for log in data["audit_logs"])


def test_citizen_save_and_remove_policy_endpoints(
    client: TestClient,
    db_session: Session,
    citizen_user: User,
    auth_headers,
):
    """Verify citizen policy bookmarking and removal endpoints."""
    policy = Policy(
        title="Higher Education Scholarship Guidelines",
        category="Education",
        status=PolicyStatus.PUBLISHED.value,
        is_active=True,
    )
    db_session.add(policy)
    db_session.commit()
    db_session.refresh(policy)

    headers = auth_headers(citizen_user)

    # 1. Bookmark the policy
    save_resp = client.post(
        "/api/v1/dashboard/citizen/saved-policies",
        json={"policy_id": policy.id, "notes": "Need to apply before next month"},
        headers=headers,
    )
    assert save_resp.status_code == 201
    assert save_resp.json()["policy_id"] == policy.id
    assert save_resp.json()["notes"] == "Need to apply before next month"

    # Verify it shows in dashboard
    dash_resp = client.get("/api/v1/dashboard/citizen", headers=headers)
    assert any(sp["policy_id"] == policy.id for sp in dash_resp.json()["saved_policies"])

    # 2. Delete bookmark
    del_resp = client.delete(f"/api/v1/dashboard/citizen/saved-policies/{policy.id}", headers=headers)
    assert del_resp.status_code == 200

    # Verify it is no longer in dashboard
    dash_resp2 = client.get("/api/v1/dashboard/citizen", headers=headers)
    assert not any(sp["policy_id"] == policy.id for sp in dash_resp2.json()["saved_policies"])


def test_citizen_submit_application_endpoint(
    client: TestClient,
    db_session: Session,
    citizen_user: User,
    auth_headers,
):
    """Verify citizen application submission and tracking endpoint."""
    scheme = Scheme(
        name="Digital India Skill Development",
        category="Employment Programs",
        status=SchemeStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(scheme)
    db_session.commit()
    db_session.refresh(scheme)

    headers = auth_headers(citizen_user)

    app_resp = client.post(
        "/api/v1/dashboard/citizen/applications",
        json={
            "scheme_id": scheme.id,
            "details_json": json.dumps({"course": "Python Cloud Developer", "center": "Delhi"}),
            "remarks": "Self-sponsored application",
        },
        headers=headers,
    )
    assert app_resp.status_code == 201
    app_data = app_resp.json()
    assert app_data["scheme_id"] == scheme.id
    assert app_data["scheme_name"] == "Digital India Skill Development"
    assert app_data["status"] == "SUBMITTED"
    assert app_data["application_number"].startswith("APP-")

    # Verify it appears in the citizen dashboard
    dash_resp = client.get("/api/v1/dashboard/citizen", headers=headers)
    assert dash_resp.status_code == 200
    assert any(a["id"] == app_data["id"] for a in dash_resp.json()["application_status"])
