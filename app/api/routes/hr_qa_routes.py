import os
from typing import Any

from fastapi import APIRouter, Body, HTTPException, status

from app.core.logging import get_logger
from app.service.hr_qa_service import HRQuestionAnswerService

router = APIRouter(
    prefix="/api/hr-qa",
    tags=["hr question answer"],
    responses={404: {"description": "Not found"}}
)


logger = get_logger(__name__)

@router.post("/answer",
            response_model=dict[str, Any],
            summary="Get HR policy answer",
            description="Processes HR-related questions using RAG system",
            responses={
                200: {"description": "Successful response with answer"},
                400: {"description": "Invalid input format"},
                500: {"description": "Internal processing error"}
            })
async def hr_qa_check(request:str = Body(...)):
    """
    Endpoint for handling HR policy questions
    
    Args:
        request: QARequest model containing user query
    
    Returns:
        Standardized QAResponse with answer or error details
    """
    try:
        logger.info(f"Processing HR query: {request[:50]}...")
        
        # Initialize service (consider dependency injection for production)
        service = HRQuestionAnswerService()
        
        # Get processed answer
        answer = service.get_answer(request)
        
        if not answer:
            logger.warning("Received empty answer for query")
            return {
            "status": "Failed",
            "response": "now answer",
            "message": "Job analysis completed successfully"
        }
        
        logger.debug(f"Successfully processed query: {request[:30]}...")
        return {
            "status": "success",
            "response": answer,
            "message": "Job analysis completed successfully"
        }

    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        ) from ve
    except Exception as e:
        logger.exception(f"Failed to process query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing request"
        ) from e