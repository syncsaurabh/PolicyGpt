from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.faq import FAQ
from app.models.feedback import Feedback, FeedbackPriority, FeedbackStatus, FeedbackType
from app.models.user import User


def test_citizen_submit_and_list_feedback(
    client: TestClient,
    citizen_user: User,
    auth_headers,
):
    headers = auth_headers(citizen_user)

    # 1. Citizen creates FEEDBACK
    payload_feedback = {
        "subject": "Suggestion for PolicyGPT",
        "description": "Please improve the policy search filters.",
        "type": "FEEDBACK",
        "category": "Suggestion",
        "rating": 5,
        "priority": "LOW",
    }
    resp1 = client.post("/api/v1/feedback", json=payload_feedback, headers=headers)
    assert resp1.status_code == 201
    data1 = resp1.json()
    assert data1["subject"] == "Suggestion for PolicyGPT"
    assert data1["feedback_type"] == "FEEDBACK"
    assert data1["type"] == "FEEDBACK"
    assert data1["content"] == "Please improve the policy search filters."
    assert data1["description"] == "Please improve the policy search filters."
    assert data1["status"] in ("SUBMITTED", "OPEN")
    feedback_id = data1["id"]

    # 2. Citizen creates ISSUE
    payload_issue = {
        "subject": "Unable to submit application",
        "description": "Application submission is failing with timeout error.",
        "type": "ISSUE",
        "priority": "HIGH",
    }
    resp2 = client.post("/api/v1/feedback", json=payload_issue, headers=headers)
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["subject"] == "Unable to submit application"
    assert data2["feedback_type"] == "ISSUE"
    assert data2["priority"] == "HIGH"

    # 3. Citizen creates SUPPORT ticket with optional application reference ID
    payload_support = {
        "subject": "Need help with application status",
        "description": "I need help understanding my application timeline.",
        "type": "SUPPORT",
        "category": "APPLICATION",
        "reference_id": "APP-2026-9901",
        "priority": "MEDIUM",
    }
    resp3 = client.post("/api/v1/feedback", json=payload_support, headers=headers)
    assert resp3.status_code == 201
    data3 = resp3.json()
    assert data3["subject"] == "Need help with application status"
    assert data3["feedback_type"] == "SUPPORT"
    assert data3["category"] == "APPLICATION"
    assert "APP-2026-9901" in data3["content"]

    # 4. View own feedback list
    my_resp = client.get("/api/v1/feedback/my", headers=headers)
    assert my_resp.status_code == 200
    my_data = my_resp.json()
    assert my_data["total_count"] >= 3
    assert any(f["id"] == feedback_id for f in my_data["results"])

    # 5. View single feedback
    single_resp = client.get(f"/api/v1/feedback/{feedback_id}", headers=headers)
    assert single_resp.status_code == 200
    assert single_resp.json()["id"] == feedback_id


def test_feedback_isolation_and_rbac(
    client: TestClient,
    db_session: Session,
    citizen_user: User,
    guest_user: User,
    admin_user: User,
    auth_headers,
):
    # Create feedback owned by citizen
    fb = Feedback(
        user_id=citizen_user.id,
        subject="Private Citizen Query",
        content="Personal confidential query content",
        feedback_type=FeedbackType.SUPPORT.value,
        status=FeedbackStatus.SUBMITTED.value,
        priority=FeedbackPriority.MEDIUM.value,
    )
    db_session.add(fb)
    db_session.commit()
    db_session.refresh(fb)

    cit_headers = auth_headers(citizen_user)
    guest_headers = auth_headers(guest_user)
    adm_headers = auth_headers(admin_user)

    # 1. Other citizen/guest tries to access citizen's ticket -> 403 Forbidden
    other_resp = client.get(f"/api/v1/feedback/{fb.id}", headers=guest_headers)
    assert other_resp.status_code == 403

    # 2. Citizen / guest tries admin feedback list -> 403 Forbidden
    cit_admin_list = client.get("/api/v1/feedback", headers=cit_headers)
    assert cit_admin_list.status_code == 403

    # 3. Admin can list all feedback
    adm_list = client.get("/api/v1/feedback?feedback_type=SUPPORT", headers=adm_headers)
    assert adm_list.status_code == 200
    assert adm_list.json()["total_count"] >= 1

    # 4. Citizen tries to update status -> 403 Forbidden
    cit_upd = client.put(f"/api/v1/feedback/{fb.id}/status", json={"status": "IN_REVIEW"}, headers=cit_headers)
    assert cit_upd.status_code == 403

    # 5. Citizen tries to resolve ticket -> 403 Forbidden
    cit_res = client.post(f"/api/v1/feedback/{fb.id}/resolve", json={"resolution": "Resolved"}, headers=cit_headers)
    assert cit_res.status_code == 403


def test_admin_resolve_and_history_workflow(
    client: TestClient,
    db_session: Session,
    citizen_user: User,
    admin_user: User,
    guest_user: User,
    auth_headers,
):
    # Citizen submits feedback
    fb = Feedback(
        user_id=citizen_user.id,
        subject="Inquiry on Education Scheme",
        content="When will the scholarship application deadline close?",
        feedback_type=FeedbackType.SUPPORT.value,
        status=FeedbackStatus.SUBMITTED.value,
        priority=FeedbackPriority.MEDIUM.value,
    )
    db_session.add(fb)
    db_session.commit()
    db_session.refresh(fb)

    adm_headers = auth_headers(admin_user)
    cit_headers = auth_headers(citizen_user)
    other_headers = auth_headers(guest_user)

    # Admin updates status to IN_PROGRESS / IN_REVIEW
    update_resp = client.put(
        f"/api/v1/feedback/{fb.id}/status",
        json={"status": "IN_REVIEW", "priority": "HIGH"},
        headers=adm_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "IN_REVIEW"
    assert update_resp.json()["priority"] == "HIGH"

    # Admin posts resolution response using 'resolution' field
    resolve_resp = client.post(
        f"/api/v1/feedback/{fb.id}/resolve",
        json={"resolution": "The scholarship deadline is extended until October 31st."},
        headers=adm_headers,
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "RESOLVED"
    assert "October 31st" in resolve_resp.json()["admin_response"]
    assert "October 31st" in resolve_resp.json()["resolution"]

    # Verify citizen can see the resolution response
    cit_check = client.get(f"/api/v1/feedback/{fb.id}", headers=cit_headers)
    assert cit_check.status_code == 200
    assert cit_check.json()["status"] == "RESOLVED"
    assert cit_check.json()["admin_response"] is not None

    # Verify notification was generated for the citizen
    notif_resp = client.get("/api/v1/notifications", headers=cit_headers)
    assert notif_resp.status_code == 200
    assert any("Query Resolved" in n["title"] for n in notif_resp.json()["results"])

    # Verify ticket history endpoint
    hist_resp = client.get(f"/api/v1/feedback/{fb.id}/history", headers=cit_headers)
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["feedback_id"] == fb.id
    assert hist_data["total_events"] >= 2  # Updated and Resolved

    # Verify other citizen cannot access history
    other_hist = client.get(f"/api/v1/feedback/{fb.id}/history", headers=other_headers)
    assert other_hist.status_code == 403


def test_feedback_validation_errors(
    client: TestClient,
    citizen_user: User,
    admin_user: User,
    auth_headers,
):
    cit_headers = auth_headers(citizen_user)
    adm_headers = auth_headers(admin_user)

    # 1. Invalid feedback type
    invalid_type_resp = client.post(
        "/api/v1/feedback",
        json={"subject": "Test", "description": "Valid content", "type": "INVALID_TYPE"},
        headers=cit_headers,
    )
    assert invalid_type_resp.status_code == 422

    # 2. Invalid priority
    invalid_pri_resp = client.post(
        "/api/v1/feedback",
        json={"subject": "Test", "description": "Valid content", "priority": "SUPER_URGENT"},
        headers=cit_headers,
    )
    assert invalid_pri_resp.status_code == 422

    # 3. Empty description / content
    empty_desc_resp = client.post(
        "/api/v1/feedback",
        json={"subject": "Test", "description": "   "},
        headers=cit_headers,
    )
    assert empty_desc_resp.status_code == 422

    # 4. Invalid status in update
    invalid_status_resp = client.put(
        "/api/v1/feedback/1/status",
        json={"status": "NON_EXISTENT_STATUS"},
        headers=adm_headers,
    )
    assert invalid_status_resp.status_code == 422


def test_faq_public_and_admin_crud(
    client: TestClient,
    admin_user: User,
    citizen_user: User,
    auth_headers,
):
    adm_headers = auth_headers(admin_user)
    cit_headers = auth_headers(citizen_user)

    # Admin creates FAQ
    create_payload = {
        "question": "How do I check my scheme eligibility?",
        "answer": "Use the Eligibility Checker tool in the main navigation menu.",
        "category": "Eligibility",
        "is_active": True,
        "display_order": 1,
    }
    create_resp = client.post("/api/v1/faqs", json=create_payload, headers=adm_headers)
    assert create_resp.status_code == 201
    faq_id = create_resp.json()["id"]

    # Citizen cannot create FAQ -> 403
    cit_create = client.post("/api/v1/faqs", json=create_payload, headers=cit_headers)
    assert cit_create.status_code == 403

    # Public/Citizen lists FAQs
    list_resp = client.get("/api/v1/faqs?category=Eligibility")
    assert list_resp.status_code == 200
    assert list_resp.json()["total_count"] >= 1
    assert any(f["id"] == faq_id for f in list_resp.json()["results"])

    # Admin updates FAQ
    upd_resp = client.put(
        f"/api/v1/faqs/{faq_id}",
        json={"answer": "Updated answer with step-by-step guidance."},
        headers=adm_headers,
    )
    assert upd_resp.status_code == 200
    assert "step-by-step" in upd_resp.json()["answer"]

    # Citizen cannot delete FAQ -> 403
    cit_del = client.delete(f"/api/v1/faqs/{faq_id}", headers=cit_headers)
    assert cit_del.status_code == 403

    # Admin deletes FAQ
    del_resp = client.delete(f"/api/v1/faqs/{faq_id}", headers=adm_headers)
    assert del_resp.status_code == 200

    # Verify 404 after deletion
    get_resp = client.get(f"/api/v1/faqs/{faq_id}")
    assert get_resp.status_code == 404
