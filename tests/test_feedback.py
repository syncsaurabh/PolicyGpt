from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.faq import FAQ
from app.models.feedback import Feedback, FeedbackStatus, FeedbackType
from app.models.user import User


def test_citizen_submit_and_list_feedback(
    client: TestClient,
    citizen_user: User,
    auth_headers,
):
    headers = auth_headers(citizen_user)

    # Submit feedback
    payload = {
        "subject": "Portal Search Feature Issue",
        "content": "Search results take too long to load on mobile.",
        "feedback_type": "ISSUE",
        "category": "Portal Issue",
        "rating": 3,
        "priority": "MEDIUM",
    }
    resp = client.post("/api/v1/feedback", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["subject"] == "Portal Search Feature Issue"
    assert data["feedback_type"] == "ISSUE"
    assert data["status"] == "SUBMITTED"
    feedback_id = data["id"]

    # View own feedback list
    my_resp = client.get("/api/v1/feedback/my", headers=headers)
    assert my_resp.status_code == 200
    my_data = my_resp.json()
    assert my_data["total_count"] >= 1
    assert any(f["id"] == feedback_id for f in my_data["results"])

    # View single feedback
    single_resp = client.get(f"/api/v1/feedback/{feedback_id}", headers=headers)
    assert single_resp.status_code == 200
    assert single_resp.json()["id"] == feedback_id


def test_feedback_isolation_between_citizens(
    client: TestClient,
    db_session: Session,
    citizen_user: User,
    guest_user: User,
    auth_headers,
):
    # Create feedback owned by citizen
    fb = Feedback(
        user_id=citizen_user.id,
        subject="Private Citizen Query",
        content="Personal query content",
        status=FeedbackStatus.SUBMITTED.value,
    )
    db_session.add(fb)
    db_session.commit()
    db_session.refresh(fb)

    # Guest / other user tries to access citizen's feedback -> 403 Forbidden
    other_headers = auth_headers(guest_user)
    resp = client.get(f"/api/v1/feedback/{fb.id}", headers=other_headers)
    assert resp.status_code == 403


def test_admin_resolve_feedback_workflow(
    client: TestClient,
    db_session: Session,
    citizen_user: User,
    admin_user: User,
    auth_headers,
):
    # Citizen submits feedback
    fb = Feedback(
        user_id=citizen_user.id,
        subject="Inquiry on Education Scheme",
        content="When will the scholarship application deadline close?",
        feedback_type=FeedbackType.INQUIRY.value,
        status=FeedbackStatus.SUBMITTED.value,
    )
    db_session.add(fb)
    db_session.commit()
    db_session.refresh(fb)

    adm_headers = auth_headers(admin_user)
    cit_headers = auth_headers(citizen_user)

    # Admin updates status to IN_REVIEW
    update_resp = client.put(
        f"/api/v1/feedback/{fb.id}/status",
        json={"status": "IN_REVIEW", "priority": "HIGH"},
        headers=adm_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "IN_REVIEW"
    assert update_resp.json()["priority"] == "HIGH"

    # Admin posts resolution response
    resolve_resp = client.post(
        f"/api/v1/feedback/{fb.id}/resolve",
        json={"admin_response": "The scholarship deadline is extended until October 31st.", "status": "RESOLVED"},
        headers=adm_headers,
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "RESOLVED"
    assert "October 31st" in resolve_resp.json()["admin_response"]

    # Verify citizen can see the resolution response
    cit_check = client.get(f"/api/v1/feedback/{fb.id}", headers=cit_headers)
    assert cit_check.status_code == 200
    assert cit_check.json()["status"] == "RESOLVED"
    assert cit_check.json()["admin_response"] is not None

    # Verify notification was generated for the citizen
    notif_resp = client.get("/api/v1/notifications", headers=cit_headers)
    assert notif_resp.status_code == 200
    assert any("Query Resolved" in n["title"] for n in notif_resp.json()["results"])


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

    # Admin deletes FAQ
    del_resp = client.delete(f"/api/v1/faqs/{faq_id}", headers=adm_headers)
    assert del_resp.status_code == 200

    # Verify 404 after deletion
    get_resp = client.get(f"/api/v1/faqs/{faq_id}")
    assert get_resp.status_code == 404
