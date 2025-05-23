"""
HR Question Answering API Routes.

This module defines API endpoints for the HR Question Answering (QA) service.
It allows users to submit HR-related questions and receive answers generated
by the HRQuestionAnswerService, typically using a RAG (Retrieval Augmented Generation)
system based on company policies or documents.

The primary endpoint is:
    POST /api/hr-qa/answer: Submits a question and gets an answer.
"""

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
async def hr_qa_check(request: str = Body(..., description="The user's HR-related question as a plain string.", example="What is the company policy on remote work?")):
    """
    Handles HR policy-related questions and provides answers.

    This endpoint receives a user's question as a plain string in the request body.
    It then utilizes the `HRQuestionAnswerService` to find and return an appropriate
    answer based on available HR documentation or policies.

    Args:
        request (str): The user's question submitted in the request body.

    Returns:
        dict[str, Any]: A dictionary containing:
            - `status` (str): "success" or "Failed".
            - `response` (str): The answer to the question, or a message indicating no answer was found.
            - `message` (str): A descriptive message about the outcome.

    Raises:
        HTTPException:
            - 400 Bad Request: If the input question is invalid (e.g., empty, though
              primary validation might be on service level).
            - 500 Internal Server Error: If an unexpected error occurs during question
              processing or if the HR QA service fails.
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
            "message": "question answersed completed successfully"
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