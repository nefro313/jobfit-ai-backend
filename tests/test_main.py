"""
Integration Tests for FastAPI Application Endpoints.

This module contains integration tests for the main API endpoints of the
jobfit-ai-backend application. It uses FastAPI's TestClient to simulate
HTTP requests and verify responses.
"""

from fastapi.testclient import TestClient

from main import app
from tests.mock_data.mock_jd import job_description

client = TestClient(app)


def test_api_health():
    """
    Tests the /health endpoint.

    Verifies that the endpoint returns a 200 OK status and the expected
    JSON response: `{"status": "healthy"}`.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_job_posting_analyzer_route(): # Corrected typo: jop -> job, analyseer -> analyzer
    """
    Tests the /api/job-analysis/analyze endpoint.

    Sends a POST request with a sample job posting URL. Verifies that the
    endpoint returns a 200 OK status and that the 'response' field in the
    JSON payload is a non-null string, potentially containing markdown.
    """
    data={"url": "https://autonomize.keka.com/careers/jobdetails/722"}
    response = client.post("/api/job-analysis/analyze",json=data) # Use json=data for FastAPI
    assert response.status_code == 200

    content = response.json().get("response")
    assert content is not None
    assert isinstance(content, str)

    # Optional: Check if response looks like Markdown
    assert any(tag in content for tag in ["#", "*", "-", "```", "**"])  # noqa: Q000

def test_hr_qa_service_route():
    """
    Tests the /api/hr-qa/answer endpoint.

    Sends a POST request with a sample HR query. Verifies that the endpoint
    returns a 200 OK status and that the 'response' field in the JSON payload
    is a non-null string, potentially containing markdown.
    """
    data={"query": "How do you handle stress?"} # This should be a raw string as per hr_qa_routes
    response = client.post("/api/hr-qa/answer", json=data["query"]) # Send raw string in body
    assert response.status_code == 200

    content = response.json().get("response")
    assert content is not None
    assert isinstance(content, str)

    # Optional: Check if response looks like Markdown
    assert any(tag in content for tag in ["#", "*", "-", "```", "**"]) 

def test_ats_checker_route():
    """
    Tests the /api/ats-checker/check endpoint.

    Sends a POST request with a sample PDF resume file and a job description string.
    Verifies that the endpoint returns a 200 OK status and that the 'response'
    field in the JSON payload is a non-null string, potentially containing markdown.
    """
    file_path = "tests/mock_data/sample_resume.pdf"  # make sure this test file exists
    with open(file_path, "rb") as f:
        response = client.post(
            "/api/ats-checker/check",
            files={"file": ("sample_resume.pdf", f, "application/pdf")},
            data={"job_description":job_description }
        )
    assert response.status_code == 200
    content = response.json().get("response")
    assert content is not None
    assert isinstance(content, str)

    # Optional: Check if response looks like Markdown
    assert any(tag in content for tag in ["#", "*", "-", "```", "**"]) 