
import logging

from crewai import LLM

from app.core.config import settings

logger = logging.getLogger(__name__)


class GroqProvider:
    pass

class GoogleProvider:
    """Google AI provider implementation"""
    def gemini_llm(self):
        llm = LLM(
        model="gemini/gemini-2.0-flash",
        api_key= settings.GOOGLE_API_KEY
        )
        return llm


class OpenAIProvider:
    """OpenAI provider implementation"""
    pass
