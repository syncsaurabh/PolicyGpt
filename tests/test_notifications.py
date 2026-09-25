from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationType, NotificationChannel, NotificationStatus
from app.models.user import User, UserRole
from app.models.policy import Policy, PolicyStatus
from app.models.scheme import Scheme, SchemeStatus
from app.services.notification_service import NotificationService
from app.services.policy_service import PolicyService
from app.services.dashboard_service import DashboardService


def test_notification_lifecycle_and_unread_count(
    client: TestClient,
    db_session: Session,
    citizen_user: User,
    auth_headers,
):
    headers = auth_headers(citizen_user)

    # Initial unread count should be 0
    resp0 = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert resp0.status_code == 200
    assert resp0.json()["unread_count"] == 0

    # Seed 2 notifications for citizen
    n1 = Notification(
        user_id=citizen_user.id,
        title="Alert 1",
        message="Message 1",
        notification_type=NotificationType.NEW_POLICY.value,
        channel=NotificationChannel.IN_APP.value,
        is_read=False,
    )
    n2 = Notification(
        user_id=citizen_user.id,
        title="Alert 2",
        message="Message 2",
        notification_type=NotificationType.SCHEME_UPDATE.value,
        channel=NotificationChannel.IN_APP.value,
        is_read=False,
    )
    db_session.add_all([n1, n2])
    db_session.commit()
    db_session.refresh(n1)
    db_session.refresh(n2)

    # Check unread count
    resp1 = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert resp1.status_code == 200
    assert resp1.json()["unread_count"] == 2

    # List notifications with filtering
    resp2 = client.get("/api/v1/notifications", headers=headers)
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["total_count"] == 2
    assert data["unread_count"] == 2

    # Filter by notification_type
    resp_filter = client.get(f"/api/v1/notifications?notification_type={NotificationType.NEW_POLICY.value}", headers=headers)
    assert resp_filter.status_code == 200
    assert resp_filter.json()["total_count"] == 1

    # Get single notification by ID
    resp_get = client.get(f"/api/v1/notifications/{n1.id}", headers=headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["title"] == "Alert 1"

    # Mark n1 as read via PATCH
    resp3 = client.patch(f"/api/v1/notifications/{n1.id}/read", headers=headers)
    assert resp3.status_code == 200
    assert resp3.json()["is_read"] is True
    assert resp3.json()["read_at"] is not None

    # Check updated unread count
    resp4 = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert resp4.json()["unread_count"] == 1

    # Mark all read via PATCH /read-all
    resp5 = client.patch("/api/v1/notifications/read-all", headers=headers)
    assert resp5.status_code == 200

    resp6 = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert resp6.json()["unread_count"] == 0

    # Delete n1
    del_resp = client.delete(f"/api/v1/notifications/{n1.id}", headers=headers)
    assert del_resp.status_code == 200


def test_notification_user_isolation(
    client: TestClient,
    db_session: Session,
    citizen_user: User,
    government_user: User,
    auth_headers,
):
    # Create notification for government user
    n_gov = Notification(
        user_id=government_user.id,
        title="Gov Alert",
        message="Gov message",
        is_read=False,
    )
    db_session.add(n_gov)
    db_session.commit()
    db_session.refresh(n_gov)

    cit_headers = auth_headers(citizen_user)

    # Citizen tries to get Gov's notification -> 403 Forbidden
    resp_get = client.get(f"/api/v1/notifications/{n_gov.id}", headers=cit_headers)
    assert resp_get.status_code == 403

    # Citizen tries to mark Gov's notification as read -> 403 Forbidden
    resp = client.put(f"/api/v1/notifications/{n_gov.id}/read", headers=cit_headers)
    assert resp.status_code == 403

    # Citizen tries to delete Gov's notification -> 403 Forbidden
    del_resp = client.delete(f"/api/v1/notifications/{n_gov.id}", headers=cit_headers)
    assert del_resp.status_code == 403


def test_notification_preferences(client: TestClient, citizen_user: User, auth_headers):
    headers = auth_headers(citizen_user)

    # Get preferences (auto-initialized)
    resp = client.get("/api/v1/notifications/preferences", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email_enabled"] is True
    assert data["in_app_enabled"] is True
    assert data["application_updates"] is True

    # Update preferences via PUT
    update_payload = {"email_enabled": False, "deadline_reminders": False, "application_updates": False}
    resp2 = client.put("/api/v1/notifications/preferences", json=update_payload, headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["email_enabled"] is False
    assert resp2.json()["deadline_reminders"] is False
    assert resp2.json()["application_updates"] is False

    # Update preferences via PATCH
    patch_payload = {"email_enabled": True}
    resp3 = client.patch("/api/v1/notifications/preferences", json=patch_payload, headers=headers)
    assert resp3.status_code == 200
    assert resp3.json()["email_enabled"] is True


def test_admin_create_and_broadcast_notifications(
    client: TestClient,
    citizen_user: User,
    admin_user: User,
    auth_headers,
):
    adm_headers = auth_headers(admin_user)
    cit_headers = auth_headers(citizen_user)

    # Citizen cannot create notifications -> 403
    create_payload = {
        "user_id": citizen_user.id,
        "title": "Unauthorized Alert",
        "message": "Citizen cannot create this.",
        "notification_type": "GENERAL",
        "channel": "IN_APP",
    }
    cit_create_resp = client.post("/api/v1/notifications", json=create_payload, headers=cit_headers)
    assert cit_create_resp.status_code == 403

    # Admin creates targeted notification for citizen
    resp = client.post("/api/v1/notifications", json=create_payload, headers=adm_headers)
    assert resp.status_code == 201
    assert resp.json()["title"] == "Unauthorized Alert"

    # Admin broadcasts notice to CITIZEN role
    bcast_payload = {
        "title": "Portal Maintenance Announcement",
        "message": "System upgrade scheduled for Saturday midnight.",
        "notification_type": "SYSTEM_ALERT",
        "channel": "IN_APP",
        "target_roles": ["CITIZEN"],
    }
    b_resp = client.post("/api/v1/notifications/broadcast", json=bcast_payload, headers=adm_headers)
    assert b_resp.status_code == 200

    # Admin views all notifications logs
    admin_all_resp = client.get("/api/v1/notifications/admin/all", headers=adm_headers)
    assert admin_all_resp.status_code == 200
    assert admin_all_resp.json()["total_count"] >= 2

    # Citizen cannot access admin all logs
    cit_admin_resp = client.get("/api/v1/notifications/admin/all", headers=cit_headers)
    assert cit_admin_resp.status_code == 403

    # Admin triggers deadline check
    deadline_resp = client.post("/api/v1/notifications/deadline-check", headers=adm_headers)
    assert deadline_resp.status_code == 200


def test_automated_event_triggers(db_session: Session, citizen_user: User, government_user: User):
    # 1. Scheme Created Trigger
    NotificationService.trigger_scheme_created(
        db=db_session,
        scheme_id=999,
        scheme_name="National Solar Subsidy",
        department="Ministry of Renewable Energy",
    )

    # 2. Application Submitted Trigger
    NotificationService.trigger_application_submitted(
        db=db_session,
        user_id=citizen_user.id,
        application_number="APP-2026-9999",
        scheme_name="National Solar Subsidy",
    )

    # 3. Application Status Changed Trigger
    NotificationService.trigger_application_status_changed(
        db=db_session,
        user_id=citizen_user.id,
        application_number="APP-2026-9999",
        scheme_name="National Solar Subsidy",
        new_status="APPROVED",
        remarks="Verification completed successfully.",
    )

    # 4. Eligibility Match Trigger
    NotificationService.trigger_eligibility_match(
        db=db_session,
        user_id=citizen_user.id,
        matched_schemes_count=3,
    )

    # 5. Policy Review and Rejection Triggers
    NotificationService.trigger_policy_submitted(
        db=db_session,
        policy_id=888,
        policy_title="Green Energy 2030",
        author_id=government_user.id,
    )
    NotificationService.trigger_policy_rejected(
        db=db_session,
        policy_id=888,
        policy_title="Green Energy 2030",
        author_id=government_user.id,
        reason="Needs fiscal impact assessment.",
    )

    # Verify notifications were created
    unread_cit = NotificationService.get_unread_count(db=db_session, user_id=citizen_user.id)
    assert unread_cit >= 3


def test_external_dispatch_graceful_handling(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "SMTP_USERNAME", None)
    monkeypatch.setattr(settings, "SMTP_PASSWORD", None)

    # Email dispatch when SMTP credentials are None should return False without error
    email_res = NotificationService.send_email(
        to_email="test@example.com",
        subject="Test Subject",
        body="Test Body",
    )
    assert email_res is False

    # SMS dispatch when unconfigured should return False without error
    sms_res = NotificationService.send_sms(
        phone_number="+1234567890",
        message="Test SMS",
    )
    assert sms_res is False


def test_smtp_email_dispatch_success_and_error(monkeypatch):
    import smtplib
    from app.core.config import settings
    from app.services.email_service import EmailService

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "testuser@gmail.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "test-app-password")
    monkeypatch.setattr(settings, "SMTP_FROM", "testuser@gmail.com")
    monkeypatch.setattr(settings, "SMTP_TLS", True)

    sent_messages = []

    class MockSMTP:
        def __init__(self, host, port, timeout=15):
            self.host = host
            self.port = port
            self.timeout = timeout
            self.logged_in = False
            self.tls_started = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def ehlo(self):
            pass

        def starttls(self, context=None):
            self.tls_started = True

        def login(self, user, password):
            if user == "fail_auth@gmail.com":
                raise smtplib.SMTPAuthenticationError(535, b"5.7.8 Username and Password not accepted")
            self.logged_in = True

        def send_message(self, msg):
            sent_messages.append(msg)

    monkeypatch.setattr(smtplib, "SMTP", MockSMTP)

    # 1. Successful send via NotificationService
    sent = NotificationService.send_email(
        to_email="citizen@example.com",
        subject="Policy Update",
        body="A new policy has been published.",
        entity_type="Policy",
        entity_id=101,
    )
    assert sent is True
    assert len(sent_messages) == 1
    assert sent_messages[0]["To"] == "citizen@example.com"
    assert sent_messages[0]["Subject"] == "Policy Update"
    assert sent_messages[0]["From"] == "testuser@gmail.com"

    # 2. Successful direct send via EmailService
    direct_sent = EmailService.send_email(
        to_email="citizen2@example.com",
        subject="Direct Notification",
        html_content="<p>Direct HTML</p>",
        text_content="Direct text",
    )
    assert direct_sent is True
    assert len(sent_messages) == 2
    assert sent_messages[1]["To"] == "citizen2@example.com"

    # 3. Authentication failure handling
    monkeypatch.setattr(settings, "SMTP_USERNAME", "fail_auth@gmail.com")
    auth_fail = NotificationService.send_email(
        to_email="citizen@example.com",
        subject="Policy Update",
        body="A new policy has been published.",
    )
    assert auth_fail is False

    # 4. Connection / Server failure handling
    class BrokenSMTP:
        def __init__(self, *args, **kwargs):
            raise smtplib.SMTPConnectError(421, b"Service not available")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr(smtplib, "SMTP", BrokenSMTP)
    conn_fail = NotificationService.send_email(
        to_email="citizen@example.com",
        subject="Policy Update",
        body="A new policy has been published.",
    )
    assert conn_fail is False

