"""
Job Posting Analyzer Service.

This module provides the `JobPostingAnalyzer` class, which is designed to analyze
job postings from a given URL. It uses a crew of AI agents to scrape job details,
research the company, and compile comprehensive insights about the job opportunity.
"""

from typing import Any

from crewai import Agent, Crew, Task
from crewai_tools import ScrapeWebsiteTool, SerperDevTool

from app.api.error_handlers import CustomExceptionError
from app.core.config import settings
from app.core.logging import get_logger
from app.llm.provider import GoogleProvider
from app.utils.yaml_config import load_yaml_configs

logger = get_logger(__name__)

# yaml file path initialize
yaml_file_path = {
    "agents": "app/agents_config/jp_analyser/agents.yaml",
    "tasks": "app/agents_config/jp_analyser/tasks.yaml"
}

class JobPostingAnalyzer:
    """
    A class to analyze job postings by:
    1. Scraping job details from a URL
    2. Researching the company
    3. Compiling insights about the job opportunity
    
    Attributes:
        llm (Any): An instance of the language model provider (Google Gemini).
        config (dict): Loaded YAML configurations for agents and tasks.
        agents_config (dict): Specific configurations for agents, derived from `config`.
        tasks_config (dict): Specific configurations for tasks, derived from `config`.
        tools (dict[str, Any]): A dictionary of initialized tools (e.g., web scraper, search tool)
                                 for agents to use.
        agents (dict[str, Agent]): A dictionary of initialized CrewAI Agent objects.
    """
    
    def __init__(self):
        """
        Initializes the JobPostingAnalyzer.

        This constructor sets up the LLM provider (Google Gemini), loads agent and
        task configurations from specified YAML files, and initializes the necessary
        tools (web scraper, search tool) and CrewAI agents.
        """
        self.llm = GoogleProvider().gemini_llm()
        self.config = load_yaml_configs(yaml_file_path)
        self.agents_config = self.config["agents"]
        self.tasks_config = self.config ["tasks"]
        self.tools = self._initialize_tools()
        self.agents = self._initialize_agents()
        
    def _initialize_tools(self) -> dict[str, Any]:
        """
        Initializes and returns the tools required by the agents.

        Currently initializes:
        - `web_scraper`: ScrapeWebsiteTool for fetching web content.
        - `search_tool`: SerperDevTool for performing web searches.
        
        These tools are stored in and returned as a dictionary, which is assigned to `self.tools`.

        Returns:
            dict[str, Any]: A dictionary mapping tool names to their initialized instances.
        """
        return {
            "web_scraper": ScrapeWebsiteTool(),
            "search_tool": SerperDevTool(api_key=settings.SERPER_API_KEY)
        }
    
    
    def _initialize_agents(self) -> dict[str, Agent]:
        """
        Initializes and returns the CrewAI agents.

        Uses configurations from `self.agents_config`, tools from `self.tools`,
        and the LLM from `self.llm` to instantiate various agents:
        - `job_scraper`: Agent responsible for scraping job details.
        - `company_researcher`: Agent for researching company information.
        - `insights_compiler`: Agent for compiling all gathered data into a report.
        
        The initialized agents are returned as a dictionary, assigned to `self.agents`.

        Returns:
            dict[str, Agent]: A dictionary mapping agent names to their `Agent` instances.
        """
        return {
            "job_scraper": Agent(
                **self.agents_config["job_scraper_agent"],
                tools=[self.tools["web_scraper"]],
                llm=self.llm
            ),
            "company_researcher": Agent(
                **self.agents_config["company_researcher_agent"],
                tools=[self.tools["search_tool"]],
                llm=self.llm
            ),
            "insights_compiler": Agent(
                **self.agents_config["insights_compiler_agent"],
                llm=self.llm
            )
        }
    
    def _extract_company_name(self, job_details: str) -> str:
        """
        Extract company name from job details text.
        
        Args:
            job_details: Raw text containing job details
            
        Returns:
            str: Extracted company name or default if not found
        """
        extraction_methods = [
            ("Company Name:", 1),
            ("Company:", 1),
            ("Organization:", 1),
            ("Employer:", 1)
        ]
        
        for prefix, split_part in extraction_methods:
            if prefix in job_details:
                return job_details.split(prefix)[split_part].split("\n")[0].strip()
        
        logger.warning("Company name not found in job details, using default")
        return "Unknown Company"
    
    def generate_insights(self, job_url: str) -> str:
        """
        Generates comprehensive insights about a job posting from its URL.

        This method orchestrates the analysis process:
        1. Scrapes job details from the provided `job_url` using `_scrape_job_details`.
        2. Extracts the company name from the scraped details using `_extract_company_name`.
        3. Researches the company using `_research_company`.
        4. Compiles the final insights report using `_compile_insights`.
        
        Args:
            job_url (str): The URL of the job posting to analyze.
            
        Returns:
            str: A formatted insights report combining job details and company research.
            
        Raises:
            CustomExceptionError: If any step in the analysis process fails.
        """
        try:
            # Step 1: Scrape job details
            job_details = self._scrape_job_details(job_url)
            
            # Step 2: Extract company name
            company_name = self._extract_company_name(job_details)
            logger.info(f"Extracted company name: {company_name}")
            
            # Step 3: Research company
            company_research = self._research_company(company_name)
            
            # Step 4: Compile final insights
            final_insights = self._compile_insights(job_details, company_research)
            
            return final_insights
            
        except Exception as e:
            logger.error(f"Failed to generate job insights: {str(e)}")
            raise CustomExceptionError("Job analysis failed:") from e
    
    def _scrape_job_details(self, job_url: str) -> str:
        """
        Executes the job scraping task for the given URL.

        Creates a specific task for the 'job_scraper' agent using configurations
        from `self.tasks_config["scrape_job_task"]`. It then runs a temporary Crew
        with this agent and task to scrape the job details.

        Args:
            job_url (str): The URL of the job posting to scrape.

        Returns:
            str: The raw text content scraped from the job posting URL.
        """
        scrape_task = Task(
            **self.tasks_config["scrape_job_task"],
            agent=self.agents["job_scraper"]
        )
        
        scrape_crew = Crew(
            agents=[self.agents["job_scraper"]],
            tasks=[scrape_task],
            verbose=True
        )
        
        result = scrape_crew.kickoff(inputs={"job_url": job_url})
        return result.raw
    
    def _research_company(self, company_name: str) -> str:
        """
        Executes the company research task for the given company name.

        Creates a specific task for the 'company_researcher' agent using
        configurations from `self.tasks_config["research_company_task"]`.
        A temporary Crew is run with this agent and task to gather company information.

        Args:
            company_name (str): The name of the company to research.

        Returns:
            str: The raw text content of the company research findings.
        """
        research_task = Task(
            **self.tasks_config["research_company_task"],
            agent=self.agents["company_researcher"]
        )
        
        research_crew = Crew(
            agents=[self.agents["company_researcher"]],
            tasks=[research_task],
            verbose=True
        )
        
        result = research_crew.kickoff(inputs={"company_name": company_name})
        return result.raw
    
    def _compile_insights(self, job_details: str, company_research: str) -> str:
        """
        Compiles the final insights report from job details and company research.

        Creates a specific task for the 'insights_compiler' agent using
        configurations from `self.tasks_config["compile_insights_task"]`.
        A temporary Crew runs with this agent and task, taking the scraped
        job details and company research as input to produce a final report.
        
        The output is cleaned of markdown formatting.

        Args:
            job_details (str): The scraped job details text.
            company_research (str): The company research findings text.

        Returns:
            str: The compiled and cleaned insights report.
        """
        compile_task = Task(
            **self.tasks_config["compile_insights_task"],
            agent=self.agents["insights_compiler"]
        )
        
        compile_crew = Crew(
            agents=[self.agents["insights_compiler"]],
            tasks=[compile_task],
            verbose=True
        )
        
        result = compile_crew.kickoff(inputs={
            "job_details": job_details,
            "company_research": company_research
        })
        
        # Clean up markdown formatting if present
        insights = result.raw.replace("```markdown", "").replace("```", "").strip()
        return insights