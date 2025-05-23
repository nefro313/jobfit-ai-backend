
"""
HR Question Answering Service.

This module provides the `HRQuestionAnswerService` class, which uses a RAG (Retrieval
Augmented Generation) system and a crew of AI agents to answer HR-related questions.
It loads HR policy documents, processes user queries, and generates answers based on
the retrieved information and agent-based reasoning.

A singleton instance (`hr_qa_service`) is provided for easy use across the application.
"""

from crewai import Agent, Crew, Process, Task

from app.api.error_handlers import CustomExceptionError
from app.core.logging import get_logger
from app.llm.provider import GoogleProvider
from app.rag.rag_system import PDFRAGSystem
from app.schemas.rag_tool import RetrieverTool
from app.utils.yaml_config import load_yaml_configs

logger = get_logger(__name__)

class HRQuestionAnswerService:
    """
    A service class for handling HR-related questions using a multi-agent system.
    
    This service integrates a RAG system for document retrieval with a multi-agent
    system (CrewAI) to answer HR-related questions. It initializes by loading
    HR documents (e.g., a PDF), setting up a vector store for retrieval,
    and configuring a crew of AI agents (Research, Formulation, QA).

    The primary method, `get_answer`, takes a user query and returns a
    generated answer.

    Key Attributes:
        rag_system (PDFRAGSystem): Instance for loading and processing PDFs.
        llm (Any): The language model provider (e.g., Google Gemini).
        hr_tool (RetrieverTool): Tool for agents to query the HR document vector store.
        agents (dict[str, Agent]): Dictionary of initialized CrewAI agents.
        research_task (Task): Task for the research agent.
        formulation_task (Task): Task for the formulation agent.
        qa_task (Task): Task for the QA agent.
        configs (dict): Loaded YAML configurations for agents and tasks.
        agents_config (dict): Specific configurations for agents.
        tasks_config (dict): Specific configurations for tasks.
    """
    
    def __init__(self, pdf_path: str = "data/hr_qa/hr_qa.pdf"):
        """
        Initializes the HRQuestionAnswerService.

        Sets up configuration paths, initializes the RAG system, loads and processes
        the specified PDF to create a retriever tool, loads agent/task configurations,
        and initializes the LLM, agents, and tasks.

        Args:
            pdf_path (str, optional): The file path to the HR policy PDF document.
                                      Defaults to "data/hr_qa/hr_qa.pdf".
        """
        self._config_paths = { # Renamed to avoid direct use, use self.configs
            "agents": "app/agents_config/hr_qa_agent/agents.yaml",
            "tasks": "app/agents_config/hr_qa_agent/tasks.yaml"
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
        """
        Loads agent and task configurations from YAML files.

        Populates `self.configs`, `self.agents_config`, and `self.tasks_config`
        attributes based on paths defined in `self._config_paths`.

        Raises:
            CustomExceptionError: If loading or parsing YAML files fails.
        """
        try:
            self.configs = load_yaml_configs(self._config_paths)
            self.agents_config = self.configs["agents"]
            self.tasks_config = self.configs["tasks"]
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
            raise CustomExceptionError("Configuration loading failed:") from e
    
    def _initialize_llm(self) -> None:
        """
        Initializes the language model (Google Gemini) and sets it to `self.llm`.

        Raises:
            CustomExceptionError: If LLM initialization fails.
        """
        try:
            self.llm = GoogleProvider().gemini_llm()
        except Exception as e:
            logger.error(f"LLM initialization failed: {e}")
            raise CustomExceptionError("LLM initialization failed: ") from e
    
    def _initialize_retriever(self, pdf_path: str) -> None:
        """
        Initializes the document retriever from the given PDF path.

        Uses `self.rag_system` to load and process the PDF, creates a vector store,
        and sets up `self.retriever` (FAISS retriever) and `self.hr_tool` (RetrieverTool for agents).
        
        Args:
            pdf_path (str): Path to the HR PDF document.

        Raises:
            CustomExceptionError: If retriever initialization or PDF processing fails.
        """
        try:
            # self.vector_store is local to this method in the original code,
            # but self.retriever and self.hr_tool are instance attributes.
            vector_store = self.rag_system.load_and_process(pdf_path)
            logger.info("vector store created")
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            logger.info("retrieved the doc")
            self.hr_tool = RetrieverTool(retriever=retriever)
        except Exception as e:
            logger.error(f"Retriever initialization failed: {e}")
            raise CustomExceptionError("Retriever initialization failed:") from e
    
    def _initialize_agents(self) -> None:
        """
        Initializes CrewAI agents based on loaded configurations.

        Uses `self.llm`, `self.hr_tool`, and `self.agents_config` to create
        and store agents in the `self.agents` dictionary (e.g., "research",
        "formulation", "qa").

        Raises:
            CustomExceptionError: If agent initialization fails.
        """
        try:
            self.agents = {
                "research": Agent(
                    llm=self.llm,
                    tools=[self.hr_tool],
                    **self.agents_config["research_agent"]
                ),
                "formulation": Agent(
                    llm=self.llm,
                    **self.agents_config["formulation_agent"]
                ),
                "qa": Agent(
                    llm=self.llm,
                    **self.agents_config["qa_agent"]
                )
            }
        except Exception as e:
            logger.error(f"Agent initialization failed: {e}")
            raise CustomExceptionError("Agent initialization failed: ") from e
    
    def _initialize_tasks(self) -> None:
        """
        Initializes CrewAI tasks based on loaded configurations and agents.

        Uses `self.tasks_config` and `self.agents` to create and assign tasks
        like `self.research_task`, `self.formulation_task`, and `self.qa_task`.
        Sets up task contexts for sequential execution.

        Raises:
            CustomExceptionError: If task initialization fails.
        """
        try:
            self.research_task = Task(
                **self.tasks_config["research_task"],
                agent=self.agents["research"]
            )
            
            self.formulation_task = Task(
                **self.tasks_config["formulation_task"],
                agent=self.agents["formulation"],
                context=[self.research_task]
            )
            
            self.qa_task = Task(
                **self.tasks_config["qa_task"],
                agent=self.agents["qa"],
                context=[self.formulation_task]
            )
        except Exception as e:
            logger.error(f"Task initialization failed: {e}")
            raise CustomExceptionError("Task initialization failed") from e

    def get_answer(self, query: str) -> str:
        """
        Orchestrates the CrewAI agents and tasks to answer a given HR-related query.

        A Crew is formed with the initialized agents and tasks. The query is passed
        as input to the crew, which then executes its tasks sequentially.

        Args:
            query (str): The HR-related question from the user.

        Returns:
            str: The final answer generated by the QA agent in the crew.

        Raises:
            CustomExceptionError: If any error occurs during the CrewAI kickoff process
                                  or if the result format is unexpected.
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
            
            result = crew.kickoff(inputs={"query": query})
            logger.info("Successfully generated HR answer")
            return result.raw
            
        except Exception as e:
            logger.error(f"Failed to generate HR answer: {e}", exc_info=True)
            raise CustomExceptionError("HR QA service error:") from e

# Singleton instance for the service
hr_qa_service = HRQuestionAnswerService()