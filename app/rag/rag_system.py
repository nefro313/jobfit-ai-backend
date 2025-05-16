from typing import List, Optional
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader  # Better PDF parser
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from app.core.logging import get_logger  # Use your existing logger
from app.api.error_handlers import CustomExceptionError
logger = get_logger(__name__)

class PDFRAGSystem:
    """
    Enhanced RAG system optimized for 16-page PDF documents with:
    - Semantic chunking strategy
    - Page-aware processing
    - Improved text cleaning
    - Configurable parameters
    
    Args:
        chunk_size: Optimal size based on document characteristics
        chunk_overlap: Maintains context between chunks
        model_name: High-performance embedding model
    """
    
    def __init__(
        self,
        chunk_size: int = 1200,
        chunk_overlap: int = 240,
        model_name: str = "BAAI/bge-small-en-v1.5",  # Better retrieval performance
        device: str = "cpu"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedder = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "(?<=\. )", " ", ""]  # Better semantic splitting
        )

    def _clean_text(self, text: str) -> str:
        """Clean PDF text preserving structure"""
        # Remove headers/footers
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        # Preserve section breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Normalize whitespace
        return re.sub(r'\s+', ' ', text).strip()

    def _process_page(self, page_content: str, page_number: int) -> List[str]:
        """Process individual PDF pages with page-aware chunking"""
        cleaned_content = self._clean_text(page_content)
        return self.text_splitter.split_text(cleaned_content)

    def load_and_process(self, pdf_path: str) -> FAISS:
        """
        End-to-end processing pipeline:
        1. Load PDF with metadata preservation
        2. Page-based cleaning and splitting
        3. Semantic chunking
        4. Vector store creation
        """
        try:
            logger.info(f"Initializing RAG processing for {pdf_path}")
            
            # Load PDF with metadata using PyMuPDF for better text extraction
            loader = PyMuPDFLoader(pdf_path)
            pages = loader.load()
            
            logger.info(f"Loaded {len(pages)} pages from PDF")
            
            # Page-based processing
            processed_chunks = []
            for idx, page in enumerate(pages):
                chunks = self._process_page(page.page_content, idx+1)
                for chunk in chunks:
                    processed_chunks.append({
                        "text": chunk,
                        "metadata": {
                            "page": idx+1,
                            "source": pdf_path,
                            "char_length": len(chunk)
                        }
                    })
            
            logger.info(f"Generated {len(processed_chunks)} semantic chunks")
            
            # Create vector store
            return FAISS.from_texts(
                texts=[chunk["text"] for chunk in processed_chunks],
                embedding=self.embedder,
                metadatas=[chunk["metadata"] for chunk in processed_chunks]
            )
            
        except Exception as e:
            logger.error(f"RAG processing failed: {str(e)}")
            raise CustomExceptionError("RAG system error") from e

# Usage example

