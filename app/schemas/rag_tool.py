from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Any, List
from langchain.schema import Document

class RetrieverTool(BaseTool):
    """CrewAI tool wrapping a LangChain VectorStore retriever."""
    # 1) Pydantic field for holding the LangChain retriever
    retriever: Any

    # 2) Tool metadata
    name: str = "HR Retriever"
    description: str = "Fetches relevant HR documentation chunks for a given question."

    # 3) Define the schema for the single input param
    class ArgsSchema(BaseModel):
        query: str = Field(..., description="Interview question to look up")

    args_schema = ArgsSchema

    def _run(self, query: str) -> str:
        # Call the LangChain retriever
        docs: List[Document] = self.retriever.invoke(query)
        return "\n\n".join([d.page_content for d in docs])

    async def _arun(self, query: str) -> str:
        docs = await self.retriever.ainvoke(query)
        return "\n\n".join([d.page_content for d in docs])
