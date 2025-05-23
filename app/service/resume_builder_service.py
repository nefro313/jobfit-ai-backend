"""
Resume Builder Service.

This module provides the `ResumeBuilderService` class, which orchestrates a crew of AI
agents to generate tailored resumes and interview preparation materials. It takes user inputs
such as an existing resume, job posting URL, GitHub profile, and a personal write-up,
then processes these through various agents (researcher, profiler, resume strategist,
interview preparer) to produce a customized resume and related advice.

A singleton instance (`resume_builder_object`) is provided for use across the application.
"""

import json
import os
from typing import Any, Dict, Optional  # noqa: UP035

import yaml
from crewai import Agent, Crew, Task
from crewai_tools import PDFSearchTool, ScrapeWebsiteTool, SerperDevTool
from pydantic import ValidationError

from app.api.error_handlers import CustomExceptionError
from app.core.config import settings
from app.core.logging import get_logger
from app.llm.provider import GoogleProvider
from app.schemas.resume_schema import ResumeData
from app.utils.file_handler import FileHandler
from app.utils.json_validator import validate_tailor_resume_json
from app.utils.pdf import PDFProcessor
from app.utils.yaml_config import load_yaml_configs

yaml_file_path = {
    "agents": "app/agents_config/resume_builder/agents.yaml",
    "tasks": "app/agents_config/resume_builder/tasks.yaml"
}

class ResumeBuilderService:
    """
    Service class for generating personalized resumes and interview preparation
    materials using a crew of AI agents.

    The service manages several agents:
    - Researcher: Gathers information about the job and company.
    - Profiler: Analyzes the user's GitHub profile and existing resume.
    - Resume Strategist: Crafts the tailored resume content and structure.
    - Interview Preparer: Generates interview questions and advice.

    Key Attributes:
        logger (Logger): Service-specific logger instance.
        llm (Any): The language model provider instance (e.g., Google Gemini).
        search_tool (SerperDevTool): Tool for web searching.
        scrape_tool (ScrapeWebsiteTool): Tool for scraping website content.
        upload_directory (str): Directory path for storing uploaded files.
        configs (dict): Loaded YAML configurations for agents and tasks.
        agents (dict[str, Agent]): Dictionary of initialized CrewAI agents.
        tasks (dict[str, Task]): Dictionary of initialized CrewAI tasks.
    """
    def __init__(self, llm_provider: Any):
        """
        Initializes the ResumeBuilderService.

        Sets up the logger, language model provider, necessary tools (search, scrape),
        configures the upload directory for resume files, loads agent and task
        configurations from YAML, and initializes the agents and tasks.

        Args:
            llm_provider (Any): An instance of a language model provider (e.g., Google Gemini).
        """
        # Logger setup
        self.logger = get_logger(__name__)
        
        # Tools and LLM setup
        self.llm = llm_provider
        self.search_tool = SerperDevTool(api_key=settings.SERPER_API_KEY)
        self.scrape_tool = ScrapeWebsiteTool()

        # Upload directory configuration
        self.upload_directory = "data/uploads"
        os.makedirs(self.upload_directory, exist_ok=True)
        self.configs = load_yaml_configs(yaml_file_path)

        
        # Initialize agents and tools
        self.agents = self._initialize_agents()
        self.tasks = self._initialize_tasks()
    
    
    def _initialize_agents(self) -> dict[str, Agent]:
        """
        Initializes and returns the CrewAI agents for the resume building process.

        Uses configurations loaded into `self.configs["agents"]` and the initialized
        `self.llm`. Agents include a researcher, profiler, resume strategist, and
        interview preparer, each equipped with appropriate tools.

        Returns:
            dict[str, Agent]: A dictionary mapping agent names to their `Agent` instances.

        Raises:
            CustomExceptionError: If a required agent configuration key is missing.
        """
        agents_config = self.configs["agents"]
        
        try:
            agents = {
                "researcher": Agent(
                    **agents_config["researcher_agent"],
                    llm=self.llm,
                    tools=[self.scrape_tool, self.search_tool],                    
                ),
                "profiler": Agent(
                    **agents_config["profiler_agent"],
                    llm=self.llm,
                    tools=[self.scrape_tool, self.search_tool]
                ),
                "resume_strategist": Agent(
                    **agents_config["resume_strategist_agent"],
                    llm=self.llm,
                    instructions = "Always format your responses as valid JSON objects. Never include plain text.",
                    
                    tools=[self.scrape_tool, self.search_tool]
                ),
                "interview_preparer": Agent(
                    **agents_config["interview_preparer_agent"],
                    llm=self.llm,
                    tools=[self.scrape_tool, self.search_tool]
                )
            }
            return agents
        except KeyError as e:
            self.logger.error(f"Agent configuration missing: {e}")
            raise CustomExceptionError("Missing agent configuration: ") from e
    
    def _initialize_tasks(self) -> dict[str, Task]:
        """
        Initializes and returns the CrewAI tasks for the resume building process.

        Uses configurations from `self.configs["tasks"]` and the initialized agents
        from `self.agents`. Defines tasks for research, profiling, resume strategy
        (outputting JSON to `data/json/tailor_resume.json`), and interview preparation.
        Sets up dependencies (contexts) between tasks.

        Returns:
            dict[str, Task]: A dictionary mapping task names to their `Task` instances.

        Raises:
            CustomExceptionError: If a required task configuration key is missing.
        """
        tasks_config = self.configs["tasks"]
        reusume_tailor_path = "data/json/tailor_resume.json" # Define path for resume strategy output
        
        try:
            # Create tasks referencing initialized agents
            research_task = Task(
                **tasks_config["research_task"],
                agent=self.agents["researcher"],
                async_execution=True
            )
            
            profile_task = Task(
                **tasks_config["profile_task"],
                agent=self.agents["profiler"],
                async_execution=True
            )
            
            resume_strategy_task = Task(
                **tasks_config["resume_strategy_task"],
                output_json=ResumeData,
                output_file=reusume_tailor_path,
                context=[research_task, profile_task],
                agent=self.agents["resume_strategist"]
            )
            
            interview_preparation_task = Task(
                **tasks_config["interview_preparation_task"],
                context=[research_task, profile_task, resume_strategy_task],
                agent=self.agents["interview_preparer"]
            )
            
            return {
                "research": research_task,
                "profile": profile_task,
                "resume_strategy": resume_strategy_task,
                "interview_prep": interview_preparation_task
            }
        except KeyError as e:
            self.logger.error(f"Task configuration missing: {e}")
            raise CustomExceptionError("Missing task configuration: ") from e
    
    def generate_resume(
        self,
        resume_file: Any, # Should be UploadFile from FastAPI
        job_posting_url: str,
        github_url: Optional[str] = None,
        personal_writeup: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Generates a tailored resume and interview preparation materials.

        This method orchestrates the entire resume building process:
        1. Saves the uploaded resume PDF to a local directory.
        2. Initializes a `PDFSearchTool` with the saved resume.
        3. Adds the `PDFSearchTool` to the relevant agents (profiler, strategist, preparer).
        4. Creates and runs a CrewAI `Crew` with all configured agents and tasks.
        5. Inputs include the job posting URL, GitHub URL, and personal write-up.
        6. After the crew execution, it validates the JSON output from the resume strategy task.
        7. Cleans up markdown formatting from the final raw output.
        8. Loads the validated JSON data.
        9. Returns a dictionary containing the status, the markdown result, and the resume JSON data.
        10. Handles `ValidationError` for input issues and other exceptions for general errors.
        11. Cleans up temporary uploaded files in a `finally` block.

        Args:
            resume_file (Any): The uploaded resume file object (typically FastAPI's `UploadFile`).
            job_posting_url (str): URL of the target job posting.
            github_url (Optional[str]): URL of the user's GitHub profile. Defaults to None.
            personal_writeup (Optional[str]): A personal write-up or summary from the user. Defaults to None.

        Returns:
            dict[str, Any]: A dictionary with the result.
                On success: `{"status": "success", "result": <markdown_output>, "tailo_resume_json": <json_data>}`
                On error: `{"status": "error", "message": <error_message>, "details": <error_details>}`
        """
        try:
            # Process PDF file
            reusume_tailor_path = "data/json/tailor_resume.json"
            pdf_processor = PDFProcessor(resume_file)
            print(self.upload_directory)
            processed_file_path = pdf_processor.save_file(self.upload_directory)
            
            # Add PDF reading tool to agents
            pdf_search_tool = PDFSearchTool(
                pdf=processed_file_path,
                config={
                    "llm": {
                        "provider": "google",
                        "config": {
                            "model": "gemini-2.0-flash",
                            "temperature": 0.7
                        }
                    },
                    "embedder": {
                        "provider": "huggingface",
                        "config": {
                            "model": "sentence-transformers/all-MiniLM-L6-v2"
                        }
                    }
                }
            )
            
            # Update agent tools with PDF search
            for agent in [
                self.agents["profiler"], 
                self.agents["resume_strategist"], 
                self.agents["interview_preparer"]
            ]:
                agent.tools.append(pdf_search_tool)
            
            # Create Crew
            job_application_crew = Crew(
                llm=self.llm,
                agents=list(self.agents.values()),
                tasks=list(self.tasks.values()),
                verbose=True
            )
            
            # Prepare inputs
            inputs = {
                "job_posting_url": job_posting_url,
                "github_url": github_url or "",
                "personal_writeup": personal_writeup or ""
            }
            
                    
            # Execute crew workflow
            result = job_application_crew.kickoff(inputs=inputs)
            if os.path.isfile(reusume_tailor_path):
                try:
                    validate_tailor_resume_json(reusume_tailor_path)
                except Exception as e:
                    print(f"{reusume_tailor_path}--{e}")
            markdown_result_raw = result.raw


            markdown_result = markdown_result_raw.replace("```markdown", "").replace("```", "").strip()

            with open("data/json/tailor_resume.json") as json_file:
                        json_data = json.load(json_file)

            return {
                "status": "success",
                "result": markdown_result,
                "tailo_resume_json": json_data
            }
                
            
        
        except ValidationError as ve:
            self.logger.error(f"Input validation error: {ve}")
            return {
                "status": "error",
                "message": "Invalid input data",
                "details": str(ve)
            }
        except Exception as e:
            self.logger.error(f"Resume generation error: {e}")
            return {
                "status": "error",
                "message": "Failed to generate resume",
                "details": str(e)
            }
        finally:
            # Clean up temporary files if needed
            FileHandler.cleanup_temp_files(self.upload_directory)




llm_provider = GoogleProvider().gemini_llm()
resume_builder_object =  ResumeBuilderService(llm_provider)

