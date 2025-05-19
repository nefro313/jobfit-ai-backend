import os

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API settings
    API_PREFIX: str = "/api"
    
    # CORS settings
    CORS_ORIGINS: list[str] = Field(
        default_factory=list,
        env="CORS_ORIGINS",     # fix the typo here too!
    )
    
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