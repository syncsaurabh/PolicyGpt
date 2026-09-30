from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.search_history import SearchHistory
from app.models.user import User


def test_policy_search_multi_filter(client: TestClient, admin_user: User, auth_headers):
    """Policies can be searched via keywords and multiple metadata filters simultaneously."""
    headers = auth_headers(admin_user)

    # Seed target policy
    client.post(
        "/api/v1/policies",
        json={
            "title": "National Ayush Health Scheme Framework",
            "description": "Integrative healthcare and indigenous medicine infrastructure.",
            "category": "Healthcare",
            "department": "Department of Health Research",
            "ministry": "Ministry of Ayush",
            "state": "Gujarat",
            "sector": "Healthcare",
            "status": "PUBLISHED",
        },
        headers=headers,
    )

    # Multi-filter search matching the policy
    resp = client.get(
        "/api/v1/search/policies",
        params={
            "keyword": "ayush",
            "category": "Healthcare",
            "state": "Gujarat",
            "department": "Health",
            "page": 1,
            "page_size": 10,
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] >= 1
    titles = [p["title"] for p in data["results"]]
    assert any("Ayush" in t for t in titles)


def test_scheme_search_multi_filter(client: TestClient, admin_user: User, auth_headers):
    """Schemes can be searched via keywords and multiple metadata filters."""
    headers = auth_headers(admin_user)

    client.post(
        "/api/v1/schemes",
        json={
            "name": "Mahila Samriddhi Yojana",
            "description": "Microfinance assistance for women entrepreneurs in rural districts.",
            "category": "Women Empowerment",
            "department": "Women and Child Development",
            "ministry": "Ministry of Women and Child Development",
            "state": "Rajasthan",
            "sector": "Finance",
            "status": "ACTIVE",
        },
        headers=headers,
    )

    resp = client.get(
        "/api/v1/search/schemes",
        params={
            "keyword": "Samriddhi",
            "category": "Women Empowerment",
            "state": "Rajasthan",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] >= 1
    assert any("Samriddhi" in s["name"] for s in data["results"])


def test_search_no_results(client: TestClient):
    """Searching for non-matching queries returns 200 with empty results list."""
    resp = client.get(
        "/api/v1/search/policies",
        params={"keyword": "non_existent_random_search_string_xyz123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] == 0
    assert data["results"] == []


def test_search_history_recorded(client: TestClient, citizen_user: User, auth_headers, db_session: Session):
    """Executing searches automatically logs query and filters into search_history table."""
    headers = auth_headers(citizen_user)

    search_query = "Affordable Housing"
    resp = client.get(
        "/api/v1/search/schemes",
        params={"keyword": search_query, "category": "Housing"},
        headers=headers,
    )
    assert resp.status_code == 200

    # Query the search_history table
    history_entry = (
        db_session.query(SearchHistory)
        .filter(SearchHistory.user_id == citizen_user.id)
        .order_by(SearchHistory.id.desc())
        .first()
    )
    assert history_entry is not None
    assert history_entry.query == search_query
    assert history_entry.filters_json is not None
    assert "Housing" in history_entry.filters_json
