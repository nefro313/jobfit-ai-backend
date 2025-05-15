"""
ATS Checker Service Class

Provides functionality to analyze a resume against a job description
using a crew of AI agents.
"""

import io
from typing import Dict, Any, Tuple

from crewai import Agent, Task, Crew

from app.llm.provider import GoogleProvider
from app.utils.parse_pdf import extract_text_from_pdf
from app.utils.ymal_config import load_yaml_configs
from app.core.logging import get_logger
from app.api.error_handlers import CustomException

logger = get_logger(__name__)

# yaml file path initialize
yaml_file_path = {
    'agents': 'app/agents_config/ats_checker_config/agents.yaml',
    'tasks': 'app/agents_config/ats_checker_config/tasks.yaml'
}

class ATSCheckerService:
    def __init__(self):
        self.llm_provider = self._initialize_llm_provider()
        self.configs = load_yaml_configs(yaml_file_path)
        self.agents, self.tasks = self._initialize_agents_and_tasks()

    def _initialize_llm_provider(self) -> Any:
        try:
            logger.debug("Initializing LLM provider for ATS checker")
            return GoogleProvider().gemini_llm()
        except Exception as e:
            logger.error("Failed to initialize LLM provider", exc_info=True)
            raise CustomException(e)

    def _initialize_agents_and_tasks(self) -> Tuple[list, list]:
        try:
            logger.debug("Initializing ATS checker agents and tasks")
            agents_config = self.configs['agents']
            tasks_config = self.configs['tasks']

            agents = {
                'resume_parser': Agent(llm=self.llm_provider, **agents_config['resume_parser']),
                'job_description_analyzer': Agent(llm=self.llm_provider, **agents_config['job_description_analyzer']),
                'keyword_matcher': Agent(llm=self.llm_provider, **agents_config['keyword_matcher']),
                'scoring_agent': Agent(llm=self.llm_provider, **agents_config['scoring_agent']),
                'feedback_agent': Agent(llm=self.llm_provider, **agents_config['feedback_agent'])
            }

            tasks = [
                Task(**tasks_config['parse_task'], agent=agents['resume_parser']),
                Task(**tasks_config['jd_analysis_task'], agent=agents['job_description_analyzer']),
                Task(**tasks_config['match_task'], agent=agents['keyword_matcher']),
                Task(**tasks_config['score_task'], agent=agents['scoring_agent']),
                Task(**tasks_config['feedback_task'], agent=agents['feedback_agent'])
            ]

            return list(agents.values()), tasks
        except KeyError as e:
            logger.error(f"Missing configuration key: {e}", exc_info=True)
            raise CustomException(e)
        except Exception as e:
            logger.error("Failed to initialize agents or tasks", exc_info=True)
            raise CustomException(e)

    def analyze(self, file_bytes: bytes, job_description: str) -> Dict[str, Any]:
        """
        Run ATS analysis on the resume file and job description.

        Args:
            file_bytes: Resume as PDF bytes
            job_description: Job description text

        Returns:
            Dict[str, Any]: Structured results from the ATS crew
        """
        try:
            logger.info("Starting ATS compatibility analysis")
            resume_text = extract_text_from_pdf(io.BytesIO(file_bytes))
            logger.debug(f"Extracted {len(resume_text)} characters from resume")

            input_data = {
                'resume_text': resume_text,
                'job_description': job_description
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
            raise CustomException(e)
