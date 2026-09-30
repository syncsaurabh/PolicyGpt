from fastapi.testclient import TestClient


def test_openapi_schema_generation(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema
    assert "/api/v1/analytics/overview" in schema["paths"]
    assert "/api/v1/notifications" in schema["paths"]
    assert "/api/v1/reports/policies" in schema["paths"]
    assert "/api/v1/feedback" in schema["paths"]
    assert "/api/v1/faqs" in schema["paths"]
    assert "/api/v1/dashboard/citizen" in schema["paths"]
    assert "/api/v1/dashboard/government" in schema["paths"]
    assert "/api/v1/dashboard/admin" in schema["paths"]
