"""
Job Posting Analyzer API Routes.

This module provides API endpoints for the Job Posting Analyzer service.
It allows users to submit a URL of a job posting, which is then analyzed
to extract details, research the company, and compile a comprehensive report.

The primary endpoint is:
    POST /api/job-analysis/analyze: Submits a job posting URL for analysis.
"""

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from app.core.logging import get_logger
from app.service.jp_analyser import JobPostingAnalyzer

router = APIRouter(
    prefix="/api/job-analysis",
    tags=["job_posting_analysis"],
    responses={404: {"description": "Not found"}}
)

logger = get_logger(__name__)

# Initialize the analyzer once when the module loads
analyzer = JobPostingAnalyzer()

@router.post(
    "/analyze",
    summary="Analyze a job posting",
    description="""Analyzes a job posting URL and returns comprehensive insights including:
    - Job details extraction
    - Company research
    - Compiled insights report""",
    response_description="Job insights analysis report",
    response_model=dict[str, Any]
)
async def analyze_job_posting(url: str = Body(..., description="The URL of the job posting to be analyzed.", example="https://www.linkedin.com/jobs/view/1234567890")):
    """
    Analyzes a given job posting URL to extract and report insights.

    This endpoint expects a JSON request body containing the `url` of the job posting.
    It uses the `JobPostingAnalyzer` service to:
    - Extract job details from the URL.
    - Perform company research.
    - Compile a comprehensive insights report.

    Args:
        url (str): The URL of the job posting, provided in the request body.

    Returns:
        dict[str, Any]: A dictionary structured as:
            - `status` (str): "success"
            - `response` (dict): The generated insights from the job posting.
            - `message` (str): "Job analysis completed successfully"

    Raises:
        HTTPException:
            - 500 Internal Server Error: If any error occurs during the analysis process.
              The error detail will contain:
                - `status` (str): "error"
                - `message` (str): "Failed to analyze job posting"
                - `error` (str): The specific error message.
    """
    try:
        logger.info(f"Starting analysis for job posting URL: {url}")
        
        # Generate insights using the analyzer service
        insights = analyzer.generate_insights(url)
        
        logger.info("Successfully generated job insights")
        return {
            "status": "success",
            "response": insights,
            "message": "Job analysis completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Job analysis failed for URL {url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to analyze job posting",
                "error": str(e)
            }
        ) from e