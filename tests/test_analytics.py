from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.policy import Policy, PolicyStatus
from app.models.scheme import Scheme, SchemeStatus
from app.models.search_history import SearchHistory
from app.models.user import User


def test_analytics_overview(client: TestClient, db_session: Session, admin_user: User, auth_headers):
    # Seed a policy and a scheme
    p = Policy(title="Analytics Policy 1", category="Education", department="Ministry of Education", status=PolicyStatus.PUBLISHED.value)
    s = Scheme(name="Analytics Scheme 1", category="Scholarships", department="Ministry of Education", status=SchemeStatus.ACTIVE.value)
    db_session.add_all([p, s])
    db_session.commit()

    headers = auth_headers(admin_user)
    response = client.get("/api/v1/analytics/overview", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_policies" in data
    assert data["total_policies"] >= 1
    assert "total_schemes" in data
    assert data["total_schemes"] >= 1
    assert "total_users" in data
    assert isinstance(data["policy_category_distribution"], list)
    assert isinstance(data["department_distribution"], list)


def test_analytics_policies(client: TestClient, db_session: Session, government_user: User, auth_headers):
    p1 = Policy(title="Agri Policy", category="Agriculture", department="Agri Dept", state="Punjab", status=PolicyStatus.PUBLISHED.value)
    p2 = Policy(title="Draft Agri", category="Agriculture", department="Agri Dept", state="Punjab", status=PolicyStatus.DRAFT.value)
    db_session.add_all([p1, p2])
    db_session.commit()

    headers = auth_headers(government_user)
    response = client.get("/api/v1/analytics/policies?department=Agri", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_policies"] >= 2
    assert data["published_count"] >= 1
    assert data["draft_count"] >= 1


def test_analytics_schemes(client: TestClient, db_session: Session, government_user: User, auth_headers):
    s1 = Scheme(name="Health Scheme", category="Healthcare", department="Health Dept", status=SchemeStatus.ACTIVE.value)
    s2 = Scheme(name="Archived Scheme", category="Healthcare", department="Health Dept", status=SchemeStatus.ARCHIVED.value)
    db_session.add_all([s1, s2])
    db_session.commit()

    headers = auth_headers(government_user)
    response = client.get("/api/v1/analytics/schemes", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_schemes"] >= 2
    assert data["active_count"] >= 1
    assert data["archived_count"] >= 1


def test_analytics_users_rbac(client: TestClient, admin_user: User, citizen_user: User, auth_headers):
    # Citizen cannot access user analytics
    cit_headers = auth_headers(citizen_user)
    cit_resp = client.get("/api/v1/analytics/users", headers=cit_headers)
    assert cit_resp.status_code == 403

    # Admin can access user analytics
    adm_headers = auth_headers(admin_user)
    adm_resp = client.get("/api/v1/analytics/users", headers=adm_headers)
    assert adm_resp.status_code == 200
    data = adm_resp.json()
    assert "total_users" in data
    assert "active_users" in data
    assert "by_role" in data


def test_analytics_departments(client: TestClient, db_session: Session, admin_user: User, auth_headers):
    p = Policy(title="Finance Policy", department="Ministry of Finance", status=PolicyStatus.PUBLISHED.value)
    s = Scheme(name="Loan Subsidy", department="Ministry of Finance", status=SchemeStatus.ACTIVE.value)
    db_session.add_all([p, s])
    db_session.commit()

    headers = auth_headers(admin_user)
    response = client.get("/api/v1/analytics/departments?department=Finance", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_departments"] >= 1
    dept_item = data["departments"][0]
    assert "Finance" in dept_item["department"]
    assert dept_item["policy_count"] >= 1
    assert dept_item["scheme_count"] >= 1


def test_analytics_search_and_usage(client: TestClient, db_session: Session, admin_user: User, auth_headers):
    sh = SearchHistory(query="PM Kisan", result_count=5)
    db_session.add(sh)
    db_session.commit()

    headers = auth_headers(admin_user)

    # Test Search Analytics
    s_resp = client.get("/api/v1/analytics/search", headers=headers)
    assert s_resp.status_code == 200
    s_data = s_resp.json()
    assert s_data["total_searches"] >= 1
    assert any(q["name"] == "PM Kisan" for q in s_data["popular_queries"])

    # Test Usage Analytics
    u_resp = client.get("/api/v1/analytics/usage", headers=headers)
    assert u_resp.status_code == 200
    u_data = u_resp.json()
    assert "total_activities" in u_data
    assert "total_searches" in u_data
