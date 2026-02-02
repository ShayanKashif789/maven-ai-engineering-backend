import logging
from assignments.AgenticQASystem3.agents.agent_executor import agent_executor

logger = logging.getLogger(__name__)

def run_agent(query: str) -> dict:
    """
    Safe execution boundary for agent calls.
    Never let raw exceptions leak past this point.
    """
    try:
        result = agent_executor.invoke({"input": query})
        return {"answer": result["output"]}

    except Exception:
        logger.exception("Agent execution failed")
        return {
            "status": "error",
            "message": "The system is temporarily unavailable."
        }
