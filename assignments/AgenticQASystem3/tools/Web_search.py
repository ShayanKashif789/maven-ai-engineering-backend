import logging
import requests
from typing import Optional, Dict, Any, List
from langchain.tools import tool
from assignments.config import settings
from assignments.AgenticQASystem3.tools.schemas import WebSearchInput


logger = logging.getLogger(__name__)

def truncate_text(text: str, max_chars: int = 600) -> str:
    if not text or len(text) <= max_chars:
        return text
    
    truncated = text[:max_chars].rsplit(' ', 1)[0]
    return f"{truncated}... [TRUNCATED FOR BREVITY]"


@tool("web_search", args_schema=WebSearchInput)
def web_search(
    query: str,
    num_results: int = 5
) -> Dict[str, Any]:
    """
    Searches the web using SERP API for up-to-date information.
    Use this tool ONLY when the question requires current, real-time info 
    or general knowledge not found in internal documents.
    """

    # 1. Configuration Check
    if not settings.SERP_API_KEY:
        logger.error("Web search failed: SERP_API_KEY not found in settings.")
        return {
            "status": "error",
            "tool": "web_search",
            "output": None,
            "error": "Search API is not configured on the server."
        }

    try:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "engine": "google",
            "api_key": settings.SERP_API_KEY,
            "num": num_results,
        }

        # 2. Network Request
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # 3. Data Extraction & Truncation
        # Handle the Google 'Answer Box' (Direct snippets)
        answer_box = data.get("answer_box", {})
        answer = answer_box.get("answer") or answer_box.get("snippet")
        if answer:
            answer = truncate_text(answer, max_chars=800)

        # Handle Organic Search Results
        results: List[Dict[str, str]] = []
        for r in data.get("organic_results", [])[:num_results]:
            snippet = r.get("snippet", "").replace("\n", " ").strip()
            if not snippet:
                continue

            results.append({
                "title": r.get("title", "Untitled"),
                "snippet": truncate_text(snippet, max_chars=400),
                "source": r.get("link", "")
            })

        # 4. Success Response
        if not answer and not results:
            return {
                "status": "success",
                "tool": "web_search",
                "output": "No relevant search results found.",
                "error": None
            }

        return {
            "status": "success",
            "tool": "web_search",
            "output": {
                "answer_box": answer,
                "organic_results": results
            },
            "error": None
        }

    except requests.exceptions.Timeout:
        logger.error(f"Timeout occurred during web search for query: {query}")
        return {
            "status": "error",
            "tool": "web_search",
            "output": None,
            "error": "The search request timed out. Please try again later."
        }

    except Exception as e:
        logger.exception("An unexpected error occurred in web_search tool.")
        return {
            "status": "error",
            "tool": "web_search",
            "output": None,
            "error": f"Internal Search Error: {type(e).__name__}"
        }