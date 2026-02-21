import logging
import re
from typing import Optional, Tuple

from langchain_core.messages import SystemMessage, HumanMessage

from assignments.AgenticQASystem3.core.llm_factory import get_llm
from assignments.MultiAgents4.state.agent_state import AgentState
from assignments.MultiAgents4.state.research_supervisor import ResearchSupervisorState

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"[a-z0-9']+")

# Keyword sets for O(1) lookup
_VECTOR_KEYWORDS = frozenset({
    "document", "documents", "doc", "docs", "pdf", "ppt", "pptx", "slides",
    "slide", "deck", "file", "files", "attachment", "attached", "internal",
    "company", "policy", "handbook", "report", "meeting", "minutes", "notes",
    "transcript", "spec", "specs", "sop", "procedure", "wiki", "confluence",
    "notion", "kb", "knowledgebase",
})

_WEB_KEYWORDS = frozenset({
    "latest", "current", "today", "now", "recent", "news", "breaking",
    "update", "updates", "price", "prices", "stock", "weather", "forecast",
    "score", "scores", "standings", "schedule", "release", "released",
    "version", "versions", "launch", "market", "rates", "inflation", "gdp",
    "earnings",
})

_RESEARCH_NEED_KEYWORDS = frozenset({
    "research", "source", "sources", "citation", "citations", "data", "stats",
    "statistics", "evidence", "study", "studies", "paper", "papers",
    "reference", "references", "bibliography", "report", "reports",
    "benchmark", "benchmarks", "numbers", "figures", "metrics", "analysis",
    "evidence-based", "fact", "facts", "fact-check", "factcheck",
})

_VECTOR_PHRASES = (
    "uploaded file", "attached file", "the document", "in the document",
    "internal docs", "company docs", "our docs", "our policy",
    "knowledge base", "from the pdf", "in the report", "meeting notes",
)

_WEB_PHRASES = (
    "latest news", "current events", "as of today", "right now", "this week",
    "this month", "this year", "breaking news", "stock price", "weather in",
    "release date", "opening hours",
)


def _normalize_and_tokenize(text: str) -> Tuple[str, frozenset[str]]:
    lowered = text.lower().strip()
    words = _WORD_RE.findall(lowered)
    normalized = " ".join(words)
    tokens = frozenset(words)
    return normalized, tokens


def _infer_research_required(user_query: str, intent: str) -> bool:
    if intent == "research_only":
        return True
    if intent == "linkedin_post":
        normalized, tokens = _normalize_and_tokenize(user_query)
        has_research_keywords = bool(tokens & _RESEARCH_NEED_KEYWORDS)
        has_research_phrases = any(phrase in normalized for phrase in ("find sources", "with citations"))
        return has_research_keywords or has_research_phrases
    return False


def _infer_source_rule_based(user_query: str) -> Tuple[Tuple[str, ...], bool]:
    normalized, tokens = _normalize_and_tokenize(user_query)
    has_vector_words = bool(tokens & _VECTOR_KEYWORDS)
    has_web_words = bool(tokens & _WEB_KEYWORDS)
    has_vector_phrases = any(phrase in normalized for phrase in _VECTOR_PHRASES)
    has_web_phrases = any(phrase in normalized for phrase in _WEB_PHRASES)

    if has_vector_words or has_vector_phrases:
        if has_web_words or has_web_phrases:
            return ("vector", "web"), True
        return ("vector",), True
    if has_web_words or has_web_phrases:
        return ("web",), True
    return tuple(), False


def _llm_fallback_tool_classifier(user_query: str) -> str:
    try:
        llm = get_llm()

        system_prompt = """You are a routing classifier for research tools.

Choose ONE of these labels based on the user's request:
1. "vector" - Use internal or uploaded documents (company docs, PDFs, files).
2. "web" - Use public web sources for current or general information.
3. "none" - No research tool is required.

Respond with ONLY: vector, web, or none.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query),
        ]

        response = llm.invoke(messages)
        decision = response.content.strip().lower().replace("-", "_").replace(" ", "_")

        if decision.startswith("vector"):
            logger.info("LLM classified as vector for: %s...", user_query[:50])
            return "vector"
        if decision.startswith("web"):
            logger.info("LLM classified as web for: %s...", user_query[:50])
            return "web"
        return "none"

    except ImportError:
        logger.error("LLM module not configured. Falling back to 'none'.")
        return "none"
    except Exception as e:
        logger.error("LLM fallback failed: %s. Returning 'none'.", e)
        return "none"


def build_research_supervisor_state(
    user_query: str,
    intent: Optional[str] = None,
    use_llm_fallback: bool = True,
) -> ResearchSupervisorState:
    if not isinstance(user_query, str):
        logger.warning("Research supervisor received non-string user_query: %r", user_query)
        return ResearchSupervisorState(
            user_request="",
            intent=intent if intent in ("linkedin_post", "research_only", "unknown") else "unknown",
            research_required=False,
            research_source="none",
        )

    cleaned = user_query.strip()
    normalized_intent = intent if intent in ("linkedin_post", "research_only", "unknown") else "unknown"
    if not cleaned:
        return ResearchSupervisorState(
            user_request="",
            intent=normalized_intent,
            research_required=False,
            research_source="none",
        )

    research_required = _infer_research_required(cleaned, normalized_intent)
    if not research_required:
        return ResearchSupervisorState(
            user_request=cleaned,
            intent=normalized_intent,
            research_required=False,
            research_source="none",
        )

    sources, matched = _infer_source_rule_based(cleaned)
    if not matched and use_llm_fallback:
        logger.info("No keyword match found. Using LLM fallback for: %s...", cleaned[:50])
        fallback = _llm_fallback_tool_classifier(cleaned)
        sources = (fallback,) if fallback in ("vector", "web") else tuple()

    if len(sources) == 1:
        source = sources[0]
    elif len(sources) > 1:
        source = "none"
    else:
        source = "none"

    return ResearchSupervisorState(
        user_request=cleaned,
        intent=normalized_intent,
        research_required=True,
        research_source=source,
    )


def research_supervisor_node(
    state: AgentState,
    enable_llm_fallback: bool = True,
) -> AgentState:
    try:
        user_query = state.get("user_query", "")
        intent = state.get("intent")

        research_state = build_research_supervisor_state(
            user_query or "",
            intent=intent,
            use_llm_fallback=enable_llm_fallback,
        )
        state["research_required"] = research_state.research_required
        state["research_source"] = research_state.research_source
        if research_state.research_source in ("vector", "web"):
            state["research_sources"] = [research_state.research_source]
        else:
            sources, matched = _infer_source_rule_based(user_query or "")
            state["research_sources"] = list(sources) if matched and sources else None
        return state

    except (KeyError, AttributeError, TypeError) as e:
        logger.error("Research supervisor node failed with expected error: %s", e, exc_info=True)
        state["research_required"] = False
        state["research_source"] = "none"
        state["research_sources"] = None
        if not state.get("final_output"):
            state["final_output"] = "Sorry, I couldn't process your request due to a system error."
        return state
    except Exception:
        logger.exception("Research supervisor node failed with unexpected error")
        state["research_required"] = False
        state["research_source"] = "none"
        state["research_sources"] = None
        if not state.get("final_output"):
            state["final_output"] = "Sorry, I couldn't process your request due to a system error."
        return state
