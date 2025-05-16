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
        llm: The language model provider
        tools: Dictionary of available tools
        agents_config: Configuration for agents
        tasks_config: Configuration for tasks
        agents: Dictionary of initialized agents
    """
    
    def __init__(self):
        """Initialize the analyzer with LLM, tools, and configurations."""
        self.llm = GoogleProvider().gemini_llm()
        self.config = load_yaml_configs(yaml_file_path)
        self.agents_config = self.config["agents"]
        self.tasks_config = self.config ["tasks"]
        self.tools = self._initialize_tools()
        self.agents = self._initialize_agents()
        
    def _initialize_tools(self) -> dict[str, Any]:
        """
        Initialize and return the tools used by the agents.
        
        Returns:
            Dict: Dictionary of initialized tools
        """
        return {
            "web_scraper": ScrapeWebsiteTool(),
            "search_tool": SerperDevTool(api_key=settings.SERPER_API_KEY)
        }
    
    
    def _initialize_agents(self) -> dict[str, Agent]:
        """
        Initialize and return all agents with their configurations and tools.
        
        Returns:
            Dict: Dictionary of initialized agents
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
        Generate comprehensive insights about a job posting from its URL.
        
        Args:
            job_url: URL of the job posting to analyze
            
        Returns:
            str: Formatted insights report
            
        Raises:
            RuntimeError: If any step in the analysis fails
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
        """Execute job scraping task and return raw details."""
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
        """Execute company research task and return raw results."""
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
        """Compile final insights from job details and company research."""
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