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
async def request(
    file: Annotated[UploadFile, File(...)],
    job_posting_url: Annotated[str, Form()],
    github_url: Annotated[str, Form()],
    write_up: Annotated[str, Form()]
):
    if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )
    try:
        response = resume_builder_object.generate_resume(file, job_posting_url, github_url,write_up)
        print(f"DEBUG RESPONSE: {response['status']}")

        if response:
            return JSONResponse(content={
                "status": response["status"],
                "result": response["result"],
                "resume_json":response["tailo_resume_json"]
            })
        else:
            return JSONResponse(content={
                "status": "Error",
                "message": "JSON file not found."
            }, status_code=404)
            
    except FileNotFoundError as e :
        print(f"Error while responding {e}")
        return JSONResponse(content={
            "status": "error",
            "message": "JSON file not found."
        }, status_code=404)