import logging
from typing import Optional, Dict, Any, List
from langchain.tools import tool
from assignments.Assignment3.core.rag_manager import RAGManager
from assignments.AgenticQASystem3.tools.schemas import VectorSearchInput

logger = logging.getLogger(__name__)
rag_manager = RAGManager()

@tool("vector_search", args_schema=VectorSearchInput)
def vector_search(query: str, k: int = 5) -> Dict[str, Any]:
    """
    Search internal uploaded documents for relevant information.
    Use this tool ONLY when the question depends on private or company-specific documents.
    """
    try:
        if not rag_manager.vectorstore:
            logger.error("VectorSearch called but vectorstore is None")
            return {
                "status": "error",
                "tool": "vector_search",
                "output": None,
                "error": "Database connection is not initialized."
            }

        # 2. Execution
        docs = rag_manager.vectorstore.similarity_search(query, k=k)

        if not docs:
            return {
                "status": "success",
                "tool": "vector_search",
                "output": "No relevant documents found for this query.",
                "error": None
            }

        formatted_results = []
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source", "Unknown Source")
            page = doc.metadata.get("page", "N/A")
            formatted_results.append(
                f"[Doc {i+1} | Source: {source} | Page: {page}]\n{doc.page_content}"
            )

        content = "\n\n".join(formatted_results)

        return {
            "status": "success",
            "tool": "vector_search",
            "output": content,
            "error": None,
            "metadata": {"count": len(docs)} # Useful for debugging
        }

    except Exception as e:
        # Log the full stack trace for the dev team
        logger.exception(f"Unexpected error in vector_search: {str(e)}")
        return {
            "status": "error",
            "tool": "vector_search",
            "output": None,
            "error": "An internal search error occurred. Please try a different query."
        }