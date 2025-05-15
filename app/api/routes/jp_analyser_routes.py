from fastapi import APIRouter, Body, HTTPException
from app.core.logging import get_logger
from app.service.jp_analyser import JobPostingAnalyzer
from typing import Dict, Any

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
    response_model=Dict[str, Any]
)
async def analyze_job_posting(url: str = Body(...)):
    """
    Endpoint to analyze a job posting URL and generate comprehensive insights.
    
    Args:
        url: The URL of the job posting to analyze
        
    Returns:
        Dictionary containing the analysis results
        
    Raises:
        HTTPException: If analysis fails (status_code 500)
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
        )