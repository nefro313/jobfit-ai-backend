# Response models for better documentation and validation
import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator
from fastapi import UploadFile, File, HTTPException, status

from app.core.logging import get_logger
from app.api.error_handlers import CustomException

logger = get_logger(__name__)


class ATSCheckResponse(BaseModel):
    """Response model for ATS check endpoint"""
    report: Dict[str, Any] = Field(..., description="ATS compatibility report")


# Input validation models
class JobDescriptionValidator(BaseModel):
    """Validator for job description input"""
    job_description: str
    
    @field_validator('job_description')
    def validate_job_description(cls, v):
        """Validate job description has minimum length and required content"""
        if not v or len(v.strip()) < 50:
            raise ValueError("Job description is too short (minimum 50 characters required)")
        
        # Check if text contains essential job description components
        required_terms = ['requirements', 'skills', 'experience', 'qualifications']
        if not any(term in v.lower() for term in required_terms):
            raise ValueError("Job description appears to be missing key components (requirements, skills, etc.)")
        
        return v


async def validate_resume_file(file: UploadFile = File(...)) -> UploadFile:
    """
    Validate uploaded resume file.
    
    Args:
        file: Uploaded resume file
        
    Returns:
        UploadFile: Validated file object
        
    Raises:
        HTTPException: If file validation fails
    """
    # Check if file exists
    if not file:
        logger.error("No resume file provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume file is required"
        )
    
    # Check file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    if file.size > MAX_FILE_SIZE:
        logger.error(f"Resume file exceeds size limit: {file.size} bytes")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume file exceeds maximum size of 10MB"
        )
    
    # Validate file type
    allowed_types = ["application/pdf"]
    if file.content_type not in allowed_types:
        logger.error(f"Invalid file type: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted"
        )
        
    # Return validated file
    return file