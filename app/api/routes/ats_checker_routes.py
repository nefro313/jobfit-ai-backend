"""
ATS Checker API Routes.

This module provides API endpoints for the ATS (Applicant Tracking System) checker.
It allows users to upload a resume and a job description to receive an ATS
compatibility analysis, including a score and improvement suggestions.

The primary endpoint is:
    POST /api/ats-checker/check: Analyzes resume-job description compatibility.
"""

import os
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse

from app.api.error_handlers import CustomExceptionError
from app.core.logging import get_logger
from app.schemas.validator import (
    ATSCheckResponse,
    JobDescriptionValidator,
    validate_resume_file,
)
from app.service.ats_checker_service import ATSCheckerService

# Initialize module logger
logger = get_logger(__name__)
ats_service = ATSCheckerService()
# Create API router with prefix and tags for documentation
router = APIRouter(
    prefix="/api/ats-checker",
    tags=["ATS Checker"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid input"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    }
)

depends = Depends(validate_resume_file)
@router.post(
    "/check", 
    response_model=ATSCheckResponse,
    summary="Analyze resume against job description",
    description="Uploads a resume and job description for ATS compatibility analysis",
    status_code=status.HTTP_200_OK
)
async def check_resume_ats_compatibility(
    file: UploadFile = depends,
    job_description: str = Form(..., description="The full text of the job description.")
) -> ATSCheckResponse:
    """
    Analyzes a resume against a job description for ATS compatibility.

    The endpoint expects a multipart/form-data request containing:
    - `file`: The resume file (PDF format recommended, validated by `validate_resume_file`).
    - `job_description`: The full text of the job description.

    It performs the following steps:
    1. Validates the uploaded resume file (e.g., type, size).
    2. Validates the job description content.
    3. Processes the resume and job description using the ATSCheckerService.
    4. Returns an ATS compatibility report, including a score and recommendations.

    Args:
        file (UploadFile): The resume file uploaded by the user. Dependency injection
                           handles file validation (`validate_resume_file`).
        job_description (str): The job description text, submitted as form data.

    Returns:
        ATSCheckResponse: A Pydantic model containing the ATS compatibility report,
                          including overall match score and detailed feedback.
                          The actual response is a JSONResponse wrapping this model.

    Raises:
        HTTPException:
            - 400 Bad Request: If resume file or job description is invalid (e.g., empty,
              wrong format, or fails Pydantic validation).
            - 500 Internal Server Error: If an unexpected error occurs during the
              ATS analysis process or a service-level error is encountered.
    """
    logger.info(f"ATS check requested for file: {file.filename}")
    
    try:
        # Validate job description using Pydantic model
        job_validator = JobDescriptionValidator(job_description=job_description)
        validated_job_description = job_validator.job_description
        
        # Read file content
        logger.debug(f"Reading resume file: {file.filename}")
        resume_content = await file.read()
        
        # Validate file content is not empty
        if not resume_content:
            logger.error("Empty resume file content")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume file appears to be empty"
            )
        
        # Process resume through ATS checker service
        logger.debug("Calling ATS analysis service")
        report = ats_service.analyze(
            file_bytes=resume_content,
            job_description=validated_job_description
        )
        
        logger.info("ATS analysis completed successfully")

        return JSONResponse(content={
            "response": report
        }, status_code=200)        
    except CustomExceptionError as e:
        # Handle service-level exceptions
        logger.error(f"ATS service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ATS analysis error: {str(e)}"
        ) from e
    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in ATS check endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during ATS analysis"
        ) from e