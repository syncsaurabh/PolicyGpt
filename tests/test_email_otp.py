from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.otp import EmailOTP
from app.services.auth_service import hash_otp


def test_registration_creates_unverified_user_and_otp(client: TestClient, db_session: Session):
    """Test new registration creates user with is_verified=False and records EmailOTP."""
    payload = {
        "name": "OTP Citizen",
        "email": "otptest@policygpt.gov.in",
        "password": "SecurePassword123!",
        "role": "CITIZEN"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "otptest@policygpt.gov.in"
    assert data["is_verified"] is False

    # Check DB user
    db_user = db_session.query(User).filter(User.email == "otptest@policygpt.gov.in").first()
    assert db_user is not None
    assert db_user.is_verified is False

    # Check EmailOTP record created
    otp_record = db_session.query(EmailOTP).filter(EmailOTP.email == "otptest@policygpt.gov.in").first()
    assert otp_record is not None
    assert otp_record.is_used is False
    assert otp_record.attempts == 0
    assert len(otp_record.otp_hash) == 64  # SHA256 length


def test_login_blocked_for_unverified_user(client: TestClient, db_session: Session):
    """Test login is blocked with 403 Forbidden for unverified users."""
    payload = {
        "name": "Unverified User",
        "email": "unverified@policygpt.gov.in",
        "password": "SecurePassword123!",
        "role": "CITIZEN"
    }
    reg_resp = client.post("/api/v1/auth/register", json=payload)
    assert reg_resp.status_code == 201

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "unverified@policygpt.gov.in", "password": "SecurePassword123!"}
    )
    assert login_resp.status_code == 403
    assert "verify your email" in login_resp.json()["detail"].lower()


def test_verify_otp_success_and_login(client: TestClient, db_session: Session):
    """Test verifying correct OTP activates user, returns JWT, and enables normal login."""
    # 1. Register
    reg_payload = {
        "name": "Verify Success User",
        "email": "verifysuccess@policygpt.gov.in",
        "password": "SecurePassword123!",
        "role": "CITIZEN"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # 2. Set known OTP for testing
    known_otp = "852963"
    otp_record = db_session.query(EmailOTP).filter(EmailOTP.email == "verifysuccess@policygpt.gov.in").first()
    otp_record.otp_hash = hash_otp(known_otp)
    db_session.commit()

    # 3. Verify OTP
    verify_resp = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "verifysuccess@policygpt.gov.in", "otp": known_otp}
    )
    assert verify_resp.status_code == 200
    token_data = verify_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["user"]["is_verified"] is True

    # 4. Confirm user in DB is now verified
    db_user = db_session.query(User).filter(User.email == "verifysuccess@policygpt.gov.in").first()
    assert db_user.is_verified is True

    # 5. Confirm normal login now succeeds
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "verifysuccess@policygpt.gov.in", "password": "SecurePassword123!"}
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


def test_verify_otp_invalid_code(client: TestClient, db_session: Session):
    """Test verification with incorrect code returns 400 and tracks attempts."""
    reg_payload = {
        "name": "Invalid Code User",
        "email": "invalidcode@policygpt.gov.in",
        "password": "SecurePassword123!",
        "role": "CITIZEN"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Set known OTP
    known_otp = "123456"
    otp_record = db_session.query(EmailOTP).filter(EmailOTP.email == "invalidcode@policygpt.gov.in").first()
    otp_record.otp_hash = hash_otp(known_otp)
    db_session.commit()

    # Submit wrong OTP
    wrong_resp = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "invalidcode@policygpt.gov.in", "otp": "999999"}
    )
    assert wrong_resp.status_code == 400
    assert "Invalid verification code" in wrong_resp.json()["detail"]

    # Verify attempt count incremented
    db_session.refresh(otp_record)
    assert otp_record.attempts == 1


def test_verify_otp_expired_code(client: TestClient, db_session: Session):
    """Test expired OTP is rejected with 400."""
    reg_payload = {
        "name": "Expired Code User",
        "email": "expiredcode@policygpt.gov.in",
        "password": "SecurePassword123!",
        "role": "CITIZEN"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Set expired timestamp
    otp_record = db_session.query(EmailOTP).filter(EmailOTP.email == "expiredcode@policygpt.gov.in").first()
    otp_record.expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db_session.commit()

    resp = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "expiredcode@policygpt.gov.in", "otp": "123456"}
    )
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


def test_verify_otp_max_attempts_exceeded(client: TestClient, db_session: Session):
    """Test exceeding maximum attempts marks OTP as used and locks out."""
    reg_payload = {
        "name": "Max Attempts User",
        "email": "maxattempts@policygpt.gov.in",
        "password": "SecurePassword123!",
        "role": "CITIZEN"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    otp_record = db_session.query(EmailOTP).filter(EmailOTP.email == "maxattempts@policygpt.gov.in").first()
    otp_record.attempts = 5
    db_session.commit()

    resp = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "maxattempts@policygpt.gov.in", "otp": "123456"}
    )
    assert resp.status_code == 400
    assert "Maximum verification attempts exceeded" in resp.json()["detail"]


def test_resend_otp_rate_limiting(client: TestClient, db_session: Session):
    """Test resending OTP within 60s cooldown is rate-limited (429)."""
    reg_payload = {
        "name": "Resend User",
        "email": "resenduser@policygpt.gov.in",
        "password": "SecurePassword123!",
        "role": "CITIZEN"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Immediate resend should trigger 429 cooldown
    resend_resp = client.post(
        "/api/v1/auth/resend-otp",
        json={"email": "resenduser@policygpt.gov.in"}
    )
    assert resend_resp.status_code == 429
    assert "Please wait" in resend_resp.json()["detail"]

    # If we backdate the created_at by 65s, resend should succeed
    otp_record = db_session.query(EmailOTP).filter(EmailOTP.email == "resenduser@policygpt.gov.in").first()
    otp_record.created_at = datetime.now(timezone.utc) - timedelta(seconds=65)
    db_session.commit()

    resend_resp2 = client.post(
        "/api/v1/auth/resend-otp",
        json={"email": "resenduser@policygpt.gov.in"}
    )
    assert resend_resp2.status_code == 200
    assert "verification code has been sent" in resend_resp2.json()["message"]
