import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from typing import Dict, Iterable, List, Optional, Tuple

from assignments.AgenticQASystem3.tools.vector_search import vector_search
from assignments.AgenticQASystem3.tools.Web_search import web_search
from assignments.MultiAgents4.state.agent_state import AgentState

logger = logging.getLogger(__name__)

def _read_timeout() -> float:
    raw = os.environ.get("RESEARCH_TOOL_TIMEOUT_S", "22.0")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        logger.warning("Invalid RESEARCH_TOOL_TIMEOUT_S=%r. Falling back to 22.0", raw)
        return 22.0
    if value <= 0:
        logger.warning("Non-positive RESEARCH_TOOL_TIMEOUT_S=%r. Falling back to 22.0", raw)
        return 22.0
    return value


_TOOL_TIMEOUT_S: float = _read_timeout()

_VALID_SOURCES = frozenset({"vector", "web"})

def _normalize_sources(
    research_sources: Optional[Iterable[str]],
    research_source: Optional[str],
) -> List[str]:
    """
    Return an ordered, deduplicated list of valid source names.
    Logs a warning for every unrecognised source so silent drops are visible.
    """
    seen: Dict[str, None] = {}

    candidates: Iterable[str]
    if research_sources is not None:
        candidates = research_sources
    elif research_source is not None:
        candidates = [research_source]
    else:
        candidates = []

    for s in candidates:
        if s in _VALID_SOURCES:
            seen.setdefault(s, None)   # preserve insertion order, deduplicate
        else:
            logger.warning("Ignoring unrecognised research source: %r", s)

    return list(seen.keys())


def _format_web_output(payload: object) -> str:
    if payload is None:
        return "No web results."
    if isinstance(payload, str):
        return payload
    try:
        return json.dumps(payload, ensure_ascii=True, indent=2)
    except (TypeError, ValueError) as exc:
        # Log the specific error before falling back so it isn't swallowed silently
        logger.warning("Could not JSON-serialise web output (%s); falling back to str()", exc)
        return str(payload)


def _summarize_outputs(vector_text: Optional[str], web_text: Optional[str]) -> str:
    parts: List[str] = []
    if vector_text:
        parts.append("Vector Search Results:\n" + vector_text)
    if web_text:
        parts.append("Web Search Results:\n" + web_text)
    return "\n\n".join(parts) if parts else "No research results available."


def _run_vector(query: str) -> Tuple[str, Optional[str]]:
    result = vector_search(query=query, k=5)
    if result.get("status") == "success":
        return "vector", result.get("output")
    error = result.get("error") or "Vector search failed."
    return "vector", f"Vector search error: {error}"


def _run_web(query: str) -> Tuple[str, Optional[str]]:
    result = web_search(query=query, num_results=5)
    if result.get("status") == "success":
        return "web", _format_web_output(result.get("output"))
    error = result.get("error") or "Web search failed."
    return "web", f"Web search error: {error}"


def research_execution_node(state: AgentState) -> AgentState:
    """
    Execute research tools based on routing decisions and persist results.
    Uses only deterministic calls; no LLM summarization.
    """
    try:
        state["research_failed"] = False
        if not state.get("research_required"):
            return state

        sources = _normalize_sources(
            state.get("research_sources"),
            state.get("research_source"),
        )
        if not sources:
            return state

        query = state.get("user_query", "").strip()
        if not query:
            return state

        # Reset only when execution is actually about to run.
        state["vector_results"] = None
        state["web_results"] = None
        state["research_summary"] = "No research results available."

        results: Dict[str, Optional[str]] = {}

        with ThreadPoolExecutor(max_workers=len(sources)) as executor:
            future_to_source = {}
            if "vector" in sources:
                future_to_source[executor.submit(_run_vector, query)] = "vector"
            if "web" in sources:
                future_to_source[executor.submit(_run_web, query)] = "web"

            # Bound the wait for ALL futures, not just individual ones.
            # Individual future.result(timeout=...) only limits how long *we
            # block waiting to collect* — it does not cancel the thread.
            # as_completed(timeout=...) gives us a hard wall-clock ceiling for
            # the whole batch, matching the user-visible latency budget.
            try:
                completed = as_completed(future_to_source, timeout=_TOOL_TIMEOUT_S)
                for future in completed:
                    try:
                        tool, output = future.result()
                    except Exception as exc:
                        # Catch any tool-level exception (not just TimeoutError)
                        # so a single bad tool never aborts the other results.
                        source_name = future_to_source.get(future, "unknown")
                        logger.error(
                            "Research tool %r raised an exception: %s",
                            source_name,
                            exc,
                            exc_info=True,
                        )
                        continue

                    results[tool] = output

            except TimeoutError:
                logger.error(
                    "One or more research tools did not complete within %.1fs; "
                    "partial results will be used.",
                    _TOOL_TIMEOUT_S,
                )
                # NOTE: threads themselves continue running in the background —
                # Python's ThreadPoolExecutor cannot forcibly cancel threads.
                # For true cancellation, migrate to asyncio.wait_for or
                # subprocess-based tools.

        state["vector_results"] = results.get("vector")
        state["web_results"] = results.get("web")
        state["research_summary"] = _summarize_outputs(
            results.get("vector"),
            results.get("web"),
        )
        return state

    except Exception:
        logger.exception("Research execution node failed with unexpected error")
        state["research_failed"] = True
        return state
