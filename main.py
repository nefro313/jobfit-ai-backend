import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    ats_checker_routes,
    hr_qa_routes,
    jp_analyser_routes,
    resume_tailor,
)

# import logging
from app.core.config import settings
from app.core.logging import setup_logging

# Setup logging
logger = setup_logging(app_name="jobfit-ai",log_level=settings.LOG_LEVEL)

# Create FastAPI app
app = FastAPI(
    title="AI Job Application Assistant",
    description="API for job application assistance tools",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(resume_tailor.router)
app.include_router(jp_analyser_routes.router)
app.include_router(hr_qa_routes.router)
app.include_router(ats_checker_routes.router)
# app.include_router(company_research.router)

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
# Add the validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()} | Body: {await request.body()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
if __name__ == "__main__":
    logger.info("Starting AI Job Application Assistant API")
    # logger.info(f"CORS Origins type: {type(settings.CORS_ORIGINS)}")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)