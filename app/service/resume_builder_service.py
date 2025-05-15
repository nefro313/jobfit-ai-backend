import os
import yaml
from typing import Dict, Any, Optional
from pydantic import ValidationError
import json

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.resume_schema import ResumeData
from app.utils.pdf import PDFProcessor
from app.utils.json_validator import  validate_tailor_resume_json
from app.utils.file_handler import FileHandler
from app.utils.yaml_config import load_yaml_configs
from app.llm.provider import GoogleProvider

from crewai import Agent, Task, Crew, Process
from crewai_tools import (
    ScrapeWebsiteTool,
    SerperDevTool,
    PDFSearchTool
)

yaml_file_path = {
    'agents': 'app/agents_config/resume_builder/agents.yaml',
    'tasks': 'app/agents_config/resume_builder/tasks.yaml'
}

class ResumeBuilderService:
    """
    Service class for generating personalized resumes using AI agents
    """
    def __init__(self, llm_provider):
        """
        Initialize the Resume Builder Service
        
        :param llm_provider: Language Model Provider
        """
        # Logger setup
        self.logger = get_logger(__name__)
        
        # Tools and LLM setup
        self.llm = llm_provider
        self.search_tool = SerperDevTool(api_key=settings.SERPER_API_KEY)
        self.scrape_tool = ScrapeWebsiteTool()

        # Upload directory configuration
        self.upload_directory = 'data/uploads'
        os.makedirs(self.upload_directory, exist_ok=True)
        self.configs = load_yaml_configs(yaml_file_path)

        
        # Initialize agents and tools
        self.agents = self._initialize_agents()
        self.tasks = self._initialize_tasks()
    
    
    def _initialize_agents(self) -> Dict[str, Agent]:
        """
        Initialize AI agents for resume building
        
        :return: Dictionary of initialized agents
        """
        agents_config = self.configs['agents']
        
        try:
            agents = {
                'researcher': Agent(
                    **agents_config['researcher_agent'],
                    llm=self.llm,
                    tools=[self.scrape_tool, self.search_tool],                    
                ),
                'profiler': Agent(
                    **agents_config['profiler_agent'],
                    llm=self.llm,
                    tools=[self.scrape_tool, self.search_tool]
                ),
                'resume_strategist': Agent(
                    **agents_config['resume_strategist_agent'],
                    llm=self.llm,
                    instructions = "Always format your responses as valid JSON objects. Never include plain text.",
                    
                    tools=[self.scrape_tool, self.search_tool]
                ),
                'interview_preparer': Agent(
                    **agents_config['interview_preparer_agent'],
                    llm=self.llm,
                    tools=[self.scrape_tool, self.search_tool]
                )
            }
            return agents
        except KeyError as e:
            self.logger.error(f"Agent configuration missing: {e}")
            raise ValueError(f"Missing agent configuration: {e}")
    
    def _initialize_tasks(self) -> Dict[str, Task]:
        """
        Initialize tasks for resume building process
        
        :return: Dictionary of initialized tasks
        """
        tasks_config = self.configs['tasks']
        reusume_tailor_path = 'data/json/tailor_resume.json'
        
        try:
            # Create tasks referencing initialized agents
            research_task = Task(
                **tasks_config['research_task'],
                agent=self.agents['researcher'],
                async_execution=True
            )
            
            profile_task = Task(
                **tasks_config['profile_task'],
                agent=self.agents['profiler'],
                async_execution=True
            )
            
            resume_strategy_task = Task(
                **tasks_config['resume_strategy_task'],
                output_json=ResumeData,
                output_file=reusume_tailor_path,
                context=[research_task, profile_task],
                agent=self.agents['resume_strategist']
            )
            
            interview_preparation_task = Task(
                **tasks_config['interview_preparation_task'],
                context=[research_task, profile_task, resume_strategy_task],
                agent=self.agents['interview_preparer']
            )
            
            return {
                'research': research_task,
                'profile': profile_task,
                'resume_strategy': resume_strategy_task,
                'interview_prep': interview_preparation_task
            }
        except KeyError as e:
            self.logger.error(f"Task configuration missing: {e}")
            raise ValueError(f"Missing task configuration: {e}")
    
    def generate_resume(
        self, 
        resume_file: Any, 
        job_posting_url: str, 
        github_url: Optional[str] = None, 
        personal_writeup: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a tailored resume using AI agents
        
        :param resume_file: Uploaded resume file
        :param job_posting_url: URL of the job posting
        :param github_url: Optional GitHub profile URL
        :param personal_writeup: Optional personal description
        :return: Dictionary with generation results
        """
        try:
            # Process PDF file
            reusume_tailor_path = 'data/json/tailor_resume.json'
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
                self.agents['profiler'], 
                self.agents['resume_strategist'], 
                self.agents['interview_preparer']
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
                'job_posting_url': job_posting_url,
                'github_url': github_url or '',
                'personal_writeup': personal_writeup or ''
            }
            
                    
            # Execute crew workflow
            result = job_application_crew.kickoff(inputs=inputs)
            if os.path.isfile(reusume_tailor_path):
                try:
                    validate_tailor_resume_json(reusume_tailor_path)
                except Exception as e:
                    print(f'{reusume_tailor_path}--{e}')
            markdown_result_raw = result.raw


            markdown_result = markdown_result_raw.replace("```markdown", "").replace("```", "").strip()



            return {
                'status': 'success',
                'result': markdown_result,
                'output_files': 'data/json/tailor_resume.json'
            }
                
            
        
        except ValidationError as ve:
            self.logger.error(f"Input validation error: {ve}")
            return {
                'status': 'error',
                'message': 'Invalid input data',
                'details': str(ve)
            }
        except Exception as e:
            self.logger.error(f"Resume generation error: {e}")
            return {
                'status': 'error',
                'message': 'Failed to generate resume',
                'details': str(e)
            }
        finally:
            # Clean up temporary files if needed
            FileHandler.cleanup_temp_files(self.upload_directory)




llm_provider = GoogleProvider().gemini_llm()
resume_builder_object =  ResumeBuilderService(llm_provider)

