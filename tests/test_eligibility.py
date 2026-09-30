import json
from fastapi.testclient import TestClient
from app.models.user import User


def test_eligibility_matching_and_rejection(client: TestClient, admin_user: User, auth_headers):
    """
    Test eligibility engine against real database rules:
    - Scheme 1: Youth Scholarship (Age: 18-28, Student, Income <= 3L, State: Maharashtra)
    - Scheme 2: Senior Citizen Pension (Age: >= 60, Income <= 2L)
    """
    headers = auth_headers(admin_user)

    # 1. Create Scheme 1
    client.post(
        "/api/v1/schemes",
        json={
            "name": "State Youth Higher Education Scholarship",
            "category": "Scholarships",
            "department": "Higher & Technical Education",
            "state": "Maharashtra",
            "application_process": "Apply on mahadbt.maharashtra.gov.in portal with income and college admission proof.",
            "status": "ACTIVE",
            "eligibility_rules": [
                {
                    "rule_name": "Youth Age Rule",
                    "criteria_json": json.dumps({"min_age": 18, "max_age": 28}),
                    "description": "Age must be between 18 and 28.",
                },
                {
                    "rule_name": "Student Occupation and State Rule",
                    "criteria_json": json.dumps({
                        "occupation": ["student"],
                        "state": ["Maharashtra"],
                        "max_income": 300000,
                    }),
                    "description": "Must be student in Maharashtra with annual income <= 300,000.",
                },
            ],
        },
        headers=headers,
    )

    # 2. Create Scheme 2
    client.post(
        "/api/v1/schemes",
        json={
            "name": "Indira Gandhi Senior Citizen Pension",
            "category": "Senior Citizen Welfare",
            "department": "Social Justice & Empowerment",
            "application_process": "Submit application at local Taluka/Panchayat office with age proof.",
            "status": "ACTIVE",
            "eligibility_rules": [
                {
                    "rule_name": "Senior Age Requirement",
                    "criteria_json": json.dumps({"min_age": 60}),
                    "description": "Applicant must be 60 years or older.",
                },
                {
                    "rule_name": "Low Income Limit",
                    "criteria_json": json.dumps({"max_income": 200000}),
                    "description": "Annual income must be below 200,000.",
                },
            ],
        },
        headers=headers,
    )

    # Profile A: 24-year-old student from Maharashtra, income 2.5L -> Eligible for Youth Scholarship ONLY
    profile_student = {
        "age": 24,
        "gender": "male",
        "income": 250000,
        "occupation": "student",
        "education": "graduate",
        "location": "Maharashtra",
        "social_category": "General",
        "disability_status": False,
    }
    resp_student = client.post("/api/v1/eligibility/check", json=profile_student)
    assert resp_student.status_code == 200
    data_student = resp_student.json()
    assert data_student["total_matches"] >= 1
    matched_names = [s["scheme_name"] for s in data_student["eligible_schemes"]]
    assert "State Youth Higher Education Scholarship" in matched_names
    assert "Indira Gandhi Senior Citizen Pension" not in matched_names

    scholarship_result = next(
        s for s in data_student["eligible_schemes"]
        if s["scheme_name"] == "State Youth Higher Education Scholarship"
    )
    assert scholarship_result["eligible"] is True
    assert len(scholarship_result["matched_rules"]) > 0
    assert "mahadbt" in scholarship_result["application_guidance"]

    # Profile B: 65-year-old retired citizen, income 1.5L -> Eligible for Senior Citizen Pension ONLY
    profile_senior = {
        "age": 65,
        "gender": "female",
        "income": 150000,
        "occupation": "retired",
        "location": "Maharashtra",
        "social_category": "General",
        "disability_status": False,
    }
    resp_senior = client.post("/api/v1/eligibility/check", json=profile_senior)
    assert resp_senior.status_code == 200
    data_senior = resp_senior.json()
    assert data_senior["total_matches"] >= 1
    senior_names = [s["scheme_name"] for s in data_senior["eligible_schemes"]]
    assert "Indira Gandhi Senior Citizen Pension" in senior_names
    assert "State Youth Higher Education Scholarship" not in senior_names

    # Profile C: 40-year-old with high income 1,000,000 -> Neither scheme eligible
    profile_high_income = {
        "age": 40,
        "income": 1000000,
        "occupation": "engineer",
        "location": "Delhi",
    }
    resp_none = client.post("/api/v1/eligibility/check", json=profile_high_income)
    assert resp_none.status_code == 200
    data_none = resp_none.json()
    non_eligible_names = [s["scheme_name"] for s in data_none["eligible_schemes"]]
    assert "State Youth Higher Education Scholarship" not in non_eligible_names
    assert "Indira Gandhi Senior Citizen Pension" not in non_eligible_names
