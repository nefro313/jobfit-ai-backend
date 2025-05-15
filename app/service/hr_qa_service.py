import os
from typing import Dict, Any
from crewai import Agent, Task, Crew, Process
from app.llm.provider import GoogleProvider
from app.rag.rag_system import PDFRAGSystem
from app.core.logging import get_logger
from app.api.error_handlers import CustomException
from app.schemas.rag_tool import RetrieverTool
from app.utils.yaml_config import load_yaml_configs

logger = get_logger(__name__)

class HRQuestionAnswerService:
    """
    A service class for handling HR-related questions using a multi-agent system.
    
    This service utilizes three specialized agents:
    1. Research Agent - Retrieves relevant HR information
    2. Formulation Agent - Structures the information
    3. QA Agent - Generates final answers
    
    Attributes:
        config_paths (Dict): Paths to YAML configuration files
        llm: Language model instance
        vector_store: Document vector store
        retriever: Document retriever tool
        agents: Dictionary of initialized agents
        tasks: Dictionary of initialized tasks
    """
    
    def __init__(self,pdf_path: str = "data/hr_qa/hr_qa.pdf"):
        """Initialize the service with configurations, LLM, and tools."""
        self.config_paths = {
            'agents': 'app/agents_config/hr_qa_agent/agents.yaml',
            'tasks': 'app/agents_config/hr_qa_agent/tasks.yaml'
        }
        self.rag_system = PDFRAGSystem()
        self._initialize_retriever(pdf_path)
        
        # Load configurations
        self._load_configurations()
        
        # Initialize components
        self._initialize_llm()
        self._initialize_agents()
        self._initialize_tasks()
    
    def _load_configurations(self) -> None:
        """Load agent and task configurations from YAML files."""
        try:
            self.configs = load_yaml_configs(self.config_paths)
            self.agents_config = self.configs['agents']
            self.tasks_config = self.configs['tasks']
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
            raise CustomException(f"Configuration loading failed: {e}")
    
    def _initialize_llm(self) -> None:
        """Initialize the language model."""
        try:
            self.llm = GoogleProvider().gemini_llm()
        except Exception as e:
            logger.error(f"LLM initialization failed: {e}")
            raise CustomException(f"LLM initialization failed: {e}")
    
    def _initialize_retriever(self,pdf_path) -> None:
        """Initialize the document retriever."""
        try:

            self.vector_store = self.rag_system.load_and_process(pdf_path)
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            self.hr_tool = RetrieverTool(retriever=self.retriever)
        except Exception as e:
            logger.error(f"Retriever initialization failed: {e}")
            raise CustomException(f"Retriever initialization failed: {e}")
    
    def _initialize_agents(self) -> None:
        """Initialize all agents with their configurations."""
        try:
            self.agents = {
                'research': Agent(
                    llm=self.llm,
                    tools=[self.hr_tool],
                    **self.agents_config['research_agent']
                ),
                'formulation': Agent(
                    llm=self.llm,
                    **self.agents_config['formulation_agent']
                ),
                'qa': Agent(
                    llm=self.llm,
                    **self.agents_config['qa_agent']
                )
            }
        except Exception as e:
            logger.error(f"Agent initialization failed: {e}")
            raise CustomException(f"Agent initialization failed: {e}")
    
    def _initialize_tasks(self) -> None:
        """Initialize all tasks with their configurations."""
        try:
            self.research_task = Task(
                **self.tasks_config['research_task'],
                agent=self.agents['research']
            )
            
            self.formulation_task = Task(
                **self.tasks_config['formulation_task'],
                agent=self.agents['formulation'],
                context=[self.research_task]
            )
            
            self.qa_task = Task(
                **self.tasks_config['qa_task'],
                agent=self.agents['qa'],
                context=[self.formulation_task]
            )
        except Exception as e:
            logger.error(f"Task initialization failed: {e}")
            raise CustomException(f"Task initialization failed: {e}")

    def get_answer(self, query: str) -> str:
        """
        Get an HR answer for the given query using the multi-agent system.
        
        Args:
            query: The HR-related question to answer
            
        Returns:
            str: The generated answer
            
        Raises:
            CustomException: If the answer generation fails
        """
        try:
            logger.info(f"Processing HR query: {query}")
            
            crew = Crew(
                llm=self.llm,
                agents=list(self.agents.values()),
                tasks=[self.research_task, self.formulation_task, self.qa_task],
                verbose=True,
                process=Process.sequential
            )
            
            result = crew.kickoff(inputs={'query': query})
            logger.info("Successfully generated HR answer")
            return result.raw
            
        except Exception as e:
            logger.error(f"Failed to generate HR answer: {e}", exc_info=True)
            raise CustomException(f"HR QA service error: {e}")

# Singleton instance for the service
hr_qa_service = HRQuestionAnswerService()