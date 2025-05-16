from fastapi.testclient import TestClient

from main import app
from tests.mock_data.mock_jd import job_description

client = TestClient(app)


def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_jop_posting_analyseer_route():
    data={"url": "https://autonomize.keka.com/careers/jobdetails/722"}
    response = client.post("/api/job-analysis/analyze",data=data)
    assert response.status_code == 200

    content = response.json().get("response")
    assert content is not None
    assert isinstance(content, str)

    # Optional: Check if response looks like Markdown
    assert any(tag in content for tag in ["#", "*", "-", "```", "**"])  # noqa: Q000

def test_hr_qa_service_route():
    data={"query": "How do you handle stress?"}
    response = client.post("/api/hr-qa/answer",data=data)
    assert response.status_code == 200

    content = response.json().get("response")
    assert content is not None
    assert isinstance(content, str)

    # Optional: Check if response looks like Markdown
    assert any(tag in content for tag in ["#", "*", "-", "```", "**"]) 

def test_ats_checker_route():

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