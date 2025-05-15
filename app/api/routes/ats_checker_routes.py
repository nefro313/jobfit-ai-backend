"""
ATS Checker API Routes

This module defines the API endpoints for the ATS (Applicant Tracking System) checker
functionality. It provides routes to analyze resumes against job descriptions
and return compatibility scores and recommendations.

Endpoints:
    POST /check: Analyzes a resume against a job description and returns an ATS compatibility report
"""

import os
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse
from app.schemas.ats_checket_validator.validator import JobDescriptionValidator,ATSCheckResponse,validate_resume_file
from app.core.logging import get_logger
from app.service.ats_checker_service import ATSCheckerService
from app.api.error_handlers import CustomException

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


@router.post(
    "/check", 
    response_model=ATSCheckResponse,
    summary="Analyze resume against job description",
    description="Uploads a resume and job description for ATS compatibility analysis",
    status_code=status.HTTP_200_OK
)
async def check_resume_ats_compatibility(
    file: UploadFile = Depends(validate_resume_file),
    job_description: str = Form(..., description="Full job description text")
) -> Dict[str, Any]:
    """
    Analyze a resume against a job description for ATS compatibility.
    
    This endpoint:
    1. Validates the uploaded resume file
    2. Validates the job description
    3. Processes the resume through ATS simulation
    4. Returns ATS compatibility score and improvement recommendations
    
    Args:
        file: Uploaded resume (PDF format)
        job_description: Full text of the job description
        
    Returns:
        Dict containing ATS compatibility report
        
    Raises:
        HTTPException: For validation or processing errors
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
    except CustomException as e:
        # Handle service-level exceptions
        logger.error(f"ATS service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ATS analysis error: {str(e)}"
        )
    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in ATS check endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during ATS analysis"
        )