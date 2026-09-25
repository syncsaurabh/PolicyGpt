from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.policy import Policy, PolicyStatus
from app.models.scheme import Scheme, SchemeStatus
from app.models.user import User


def test_reports_json_endpoints(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    auth_headers,
):
    # Seed test data
    p = Policy(
        title="Report Test Policy",
        category="Healthcare",
        department="Ministry of Health",
        status=PolicyStatus.PUBLISHED.value,
    )
    s = Scheme(
        name="Report Test Scheme",
        category="Healthcare",
        department="Ministry of Health",
        status=SchemeStatus.ACTIVE.value,
    )
    db_session.add_all([p, s])
    db_session.commit()

    headers = auth_headers(admin_user)

    # 1. Policy Report
    p_resp = client.get("/api/v1/reports/policies?department=Health", headers=headers)
    assert p_resp.status_code == 200
    p_data = p_resp.json()
    assert p_data["record_count"] >= 1
    assert any(item["title"] == "Report Test Policy" for item in p_data["data"])

    # 2. Scheme Report
    s_resp = client.get("/api/v1/reports/schemes?category=Healthcare", headers=headers)
    assert s_resp.status_code == 200
    s_data = s_resp.json()
    assert s_data["record_count"] >= 1

    # 3. Department Report
    d_resp = client.get("/api/v1/reports/departments", headers=headers)
    assert d_resp.status_code == 200
    d_data = d_resp.json()
    assert d_data["record_count"] >= 1

    # 4. User Activity Report
    u_resp = client.get("/api/v1/reports/user-activity", headers=headers)
    assert u_resp.status_code == 200


def test_reports_pdf_export(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    auth_headers,
):
    p = Policy(title="PDF Export Policy", category="Education", department="Dept of Education", status="PUBLISHED")
    db_session.add(p)
    db_session.commit()

    headers = auth_headers(admin_user)

    # Export Policy PDF
    pdf_resp = client.get("/api/v1/reports/export/policies?format=pdf", headers=headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert b"%PDF" in pdf_resp.content[:10]  # Valid PDF binary header

    # Export Scheme PDF
    s_pdf_resp = client.get("/api/v1/reports/export/schemes?format=pdf", headers=headers)
    assert s_pdf_resp.status_code == 200
    assert s_pdf_resp.headers["content-type"] == "application/pdf"
    assert b"%PDF" in s_pdf_resp.content[:10]


def test_reports_excel_export(
    client: TestClient,
    db_session: Session,
    government_user: User,
    auth_headers,
):
    headers = auth_headers(government_user)

    # Export Policy Excel
    xlsx_resp = client.get("/api/v1/reports/export/policies?format=excel", headers=headers)
    assert xlsx_resp.status_code == 200
    assert "spreadsheetml" in xlsx_resp.headers["content-type"]
    assert xlsx_resp.content[:2] == b"PK"  # Valid ZIP / XLSX header

    # Export Department Excel
    dept_xlsx_resp = client.get("/api/v1/reports/export/departments?format=excel", headers=headers)
    assert dept_xlsx_resp.status_code == 200
    assert dept_xlsx_resp.content[:2] == b"PK"


def test_reports_history_list(
    client: TestClient,
    admin_user: User,
    auth_headers,
):
    headers = auth_headers(admin_user)
    # Trigger an export to ensure a history log exists
    client.get("/api/v1/reports/export/policies?format=pdf", headers=headers)

    # List history
    resp = client.get("/api/v1/reports", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] >= 1
    assert "results" in data
