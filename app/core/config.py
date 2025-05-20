import json
import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API settings
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list[str] = Field(
        default_factory=list,
        env="CORS_ORIGINS",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                # First try parsing as JSON
                return json.loads(v)
            except json.JSONDecodeError:
                # If that fails, try splitting by comma
                return [origin.strip() for origin in v.split(",")]
        return v
    # LLM settings
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "groq")
    #Search tool api
    SERPER_API_KEY:str = os.getenv("SERPER_API_KEY")
    

    
    # RAG settings
    HR_QA_DATASET_PATH: str = "data/hr_qa/hr_qa_dataset.pdf"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    
    class Config:
        env_file = ".env"
        model_config = {"extra": "ignore"}

settings = Settings()