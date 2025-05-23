"""
Resume Tailor API Routes.

This module defines API endpoints for the Resume Tailor service.
It allows users to upload their resume (PDF), provide a job posting URL,
a GitHub profile URL, and a custom write-up. The service then generates
a tailored resume based on these inputs.

The primary endpoint is:
    POST /api/resume-builder/check: Submits resume and details for tailoring.
"""

import json
import os
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.service.resume_builder_service import resume_builder_object

router = APIRouter(
    prefix="/api/resume-builder",
    tags=["resume_tailor"],
    responses={404: {"description": "Not found"}}
)
logger = get_logger(__name__)

@router.post("/check")
async def request(  # Consider renaming for clarity, e.g., tailor_resume_request
    file: Annotated[UploadFile, File(description="The user's current resume in PDF format.")],
    job_posting_url: Annotated[str, Form(description="URL of the target job posting.")],
    github_url: Annotated[str, Form(description="URL of the user's GitHub profile.")],
    write_up: Annotated[str, Form(description="A brief write-up or additional points from the user.")]
):
    """
    Tailors a resume based on an uploaded PDF, job posting, GitHub profile, and user write-up.

    This endpoint expects a multipart/form-data request containing:
    - `file`: The user's resume (must be a PDF).
    - `job_posting_url`: URL of the job posting to tailor the resume for.
    - `github_url`: URL of the user's GitHub profile for additional context.
    - `write_up`: User-provided text with key points or a summary.

    The service processes these inputs to generate a tailored resume.

    Args:
        file (UploadFile): The resume PDF file.
        job_posting_url (str): URL of the job posting.
        github_url (str): URL of the GitHub profile.
        write_up (str): User's custom write-up.

    Returns:
        JSONResponse: Contains the status of the operation, the tailored resume content (result),
                      and the tailored resume in JSON format (`resume_json`).
                      Example success structure:
                      {
                          "status": "success",
                          "result": "<tailored resume text/html>",
                          "resume_json": { ... }
                      }
                      Example error structure (e.g. if service indicates file not found):
                      {
                          "status": "Error" / "error",
                          "message": "JSON file not found."
                      }

    Raises:
        HTTPException:
            - 400 Bad Request: If the uploaded file is not a PDF.
            - 404 Not Found: If the resume builder service reports that a necessary
                             internal JSON file was not found (this might indicate an
                             internal server issue rather than a client one).
            - Potentially other exceptions from the underlying service if not caught.
    """
    if not file.filename.lower().endswith(".pdf"):
            logger.warning(f"Non-PDF file upload attempt: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )
    try:
        logger.info(f"Processing resume tailoring request for file: {file.filename}, job: {job_posting_url}")
        response = resume_builder_object.generate_resume(file, job_posting_url, github_url,write_up)
        # print(f"DEBUG RESPONSE: {response['status']}") # Consider removing debug print

        if response and "status" in response and "result" in response and "tailo_resume_json" in response:
            logger.info(f"Resume tailoring successful for: {file.filename}")
            return JSONResponse(content={
                "status": response["status"],
                "result": response["result"],
                "resume_json":response["tailo_resume_json"]
            })
        else:
            # This path might indicate an issue with the service's response structure
            logger.error(f"Resume builder service returned unexpected or incomplete response for {file.filename}. Response: {response}")
            return JSONResponse(content={
                "status": "Error",
                "message": "Resume generation service returned an invalid response."
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) # Changed to 500 as it's a server/service side issue
            
    except FileNotFoundError as e : # This specific exception might be too narrow or internal
        logger.error(f"Internal FileNotFoundError during resume tailoring for {file.filename}: {e}", exc_info=True)
        return JSONResponse(content={
            "status": "error",
            "message": "An internal file was not found during resume generation."
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) # Changed to 500
    except HTTPException: # Re-raise HTTPExceptions from validation etc.
        raise
    except Exception as e:
        logger.error(f"Unexpected error during resume tailoring for {file.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during resume tailoring."
        ) from e