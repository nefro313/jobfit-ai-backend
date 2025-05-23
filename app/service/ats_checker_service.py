"""
ATS Checker Service Class

Provides functionality to analyze a resume against a job description
using a crew of AI agents.
"""

import io
from typing import Any

from crewai import Agent, Crew, Task

from app.api.error_handlers import CustomExceptionError
from app.core.logging import get_logger
from app.llm.provider import GoogleProvider
from app.utils.parse_pdf import extract_text_from_pdf
from app.utils.yaml_config import load_yaml_configs

logger = get_logger(__name__)

# yaml file path initialize
yaml_file_path = {
    "agents": "app/agents_config/ats_checker_config/agents.yaml",
    "tasks": "app/agents_config/ats_checker_config/tasks.yaml"
}

class ATSCheckerService:
    """
    A service for analyzing resumes against job descriptions using a crew of AI agents.

    This service orchestrates multiple AI agents (e.g., resume parser, job description
    analyzer, keyword matcher, scoring agent, feedback agent) to perform a comprehensive
    ATS (Applicant Tracking System) compatibility check. It initializes an LLM provider,
    loads agent and task configurations from YAML files, and provides an `analyze`
    method to process resume and job description inputs.

    Attributes:
        llm_provider (Any): An instance of an LLM provider (e.g., Google Gemini).
        configs (dict): Loaded configurations for agents and tasks from YAML files.
        agents (list[Agent]): A list of initialized CrewAI Agent objects.
        tasks (list[Task]): A list of initialized CrewAI Task objects.
    """
    def __init__(self):
        """
        Initializes the ATSCheckerService.

        This constructor sets up the LLM provider, loads agent and task
        configurations from specified YAML files, and initializes the
        CrewAI agents and tasks.
        """
        self.llm_provider = self._initialize_llm_provider()
        self.configs = load_yaml_configs(yaml_file_path)
        self.agents, self.tasks = self._initialize_agents_and_tasks()

    def _initialize_llm_provider(self) -> Any:
        """
        Initializes and returns the LLM provider.

        Currently configured to use Google Gemini LLM.

        Returns:
            Any: An instance of the configured LLM provider.

        Raises:
            CustomExceptionError: If the LLM provider fails to initialize.
        """
        try:
            logger.debug("Initializing LLM provider for ATS checker")
            return GoogleProvider().gemini_llm()
        except Exception as e:
            logger.error("Failed to initialize LLM provider", exc_info=True)
            raise CustomExceptionError("Failed to initialize LLM provider") from e

    def _initialize_agents_and_tasks(self) -> tuple[list[Agent], list[Task]]:
        """
        Initializes and returns the CrewAI agents and tasks from configuration.

        Loads agent and task definitions from YAML files specified in `yaml_file_path`,
        using the `self.configs` attribute (loaded in `__init__`).
        It instantiates `Agent` and `Task` objects accordingly.

        Returns:
            tuple[list[Agent], list[Task]]: A tuple containing a list of initialized
                                           Agent objects and a list of initialized Task objects.

        Raises:
            CustomExceptionError: If there's a missing configuration key or any other
                                  error during agent/task initialization.
        """
        try:
            logger.debug("Initializing ATS checker agents and tasks")
            agents_config = self.configs["agents"]
            tasks_config = self.configs["tasks"]

            agents = {
                "resume_parser": Agent(llm=self.llm_provider, **agents_config["resume_parser"]),
                "job_description_analyzer": Agent(llm=self.llm_provider, **agents_config["job_description_analyzer"]),
                "keyword_matcher": Agent(llm=self.llm_provider, **agents_config["keyword_matcher"]),
                "scoring_agent": Agent(llm=self.llm_provider, **agents_config["scoring_agent"]),
                "feedback_agent": Agent(llm=self.llm_provider, **agents_config["feedback_agent"])
            }

            tasks = [
                Task(**tasks_config["parse_task"], agent=agents["resume_parser"]),
                Task(**tasks_config["jd_analysis_task"], agent=agents["job_description_analyzer"]),
                Task(**tasks_config["match_task"], agent=agents["keyword_matcher"]),
                Task(**tasks_config["score_task"], agent=agents["scoring_agent"]),
                Task(**tasks_config["feedback_task"], agent=agents["feedback_agent"])
            ]

            return list(agents.values()), tasks
        except KeyError as e:
            logger.error(f"Missing configuration key: {e}", exc_info=True)
            raise CustomExceptionError("Missing configuration key") from e
        except Exception as e:
            logger.error("Failed to initialize agents or tasks", exc_info=True)
            raise CustomExceptionError("Missing configuration key") from e

    def analyze(self, file_bytes: bytes, job_description: str) -> dict[str, Any]:
        """
        Runs an ATS (Applicant Tracking System) analysis on a given resume and job description.

        This method extracts text from the provided resume file (PDF bytes), then uses a
        CrewAI setup (agents and tasks) to perform the analysis against the job description.

        Args:
            file_bytes (bytes): The content of the resume file, expected in PDF format.
            job_description (str): The full text of the job description.

        Returns:
            dict[str, Any]: A dictionary containing the raw structured results from the
                            ATS analysis crew. The exact structure depends on the final
                            task output of the CrewAI setup.

        Raises:
            CustomExceptionError: If PDF text extraction fails, or if the CrewAI analysis
                                  process encounters an error.
        """
        try:
            logger.info("Starting ATS compatibility analysis")
            resume_text = extract_text_from_pdf(io.BytesIO(file_bytes))
            logger.debug(f"Extracted {len(resume_text)} characters from resume")

            input_data = {
                "resume_text": resume_text,
                "job_description": job_description
            }

            ats_crew = Crew(
                llm=self.llm_provider,
                agents=self.agents,
                tasks=self.tasks,
                verbose=True
            )

            result = ats_crew.kickoff(inputs=input_data)
            logger.info("ATS analysis completed successfully")
            return result.raw

        except Exception as e:
            logger.error(f"ATS analysis failed: {str(e)}", exc_info=True)
            raise CustomExceptionError("ATS analysis failed:") from e