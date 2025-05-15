import os
from fastapi import APIRouter,UploadFile,File, Form,HTTPException,status
from typing import Annotated

import json
from fastapi.responses import JSONResponse
from app.core.logging import get_logger


from app.service.resume_builder_service import  resume_builder_object 



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
    if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )
    try:
        response = resume_builder_object.generate_resume(file, job_posting_url, github_url,write_up)
        print(f"DEBUG RESPONSE: {response['status']}")
        
        file_path = response['output_files'] # your backend path
        print(f'FILE_PATH____{response["status"]}--{file_path}**')
        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"error": "File not found"})
        
        if response['status'] == 'success' and 'output_files' in response:
            json_file_path = response['output_files']
            if json_file_path and os.path.exists(json_file_path):

                with open(json_file_path, 'r') as json_file:
                        response['resume_data'] = json.load(json_file)
        



        # === Step 2: Return combined structured response ===
        return JSONResponse(content={
            "status": response["status"],
            "result": response["result"],
            "resume_json":response['resume_data']
        })
    except FileNotFoundError as e :
        print(f'Error while responding {e}')
        return JSONResponse(content={
            "status": "error",
            "message": "JSON file not found."
        }, status_code=404)