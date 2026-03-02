import logging
import re
from typing import Optional, Tuple

from langchain_core.messages import SystemMessage, HumanMessage
from assignments.AgenticQASystem3.core.llm_factory import get_llm
from assignments.MultiAgents4.state.agent_state import AgentState
from assignments.MultiAgents4.state.meta_supervisor import MetaSupervisorState

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"[a-z0-9']+")

# Keyword sets for O(1) lookup
_WRITING_KEYWORDS = frozenset({
    "write", "draft", "compose", "create", "craft", "edit", "polish",
    "rewrite", "improve", "refine", "shorten", "lengthen", "summarize",
})

_POST_KEYWORDS = frozenset({
    "post", "thread", "carousel", "announcement", "hook", "cta", "headline",
})

_RESEARCH_KEYWORDS = frozenset({
    "research", "citations", "citation", "sources", "source", "papers",
    "studies", "evidence", "stats", "statistics", "data", "facts",
    "literature", "survey",
})

# Phrase tuples for faster iteration
_LINKEDIN_PHRASES = (
    "linkedin", "linked in", "li post", "post on linkedin",
)

_RESEARCH_PHRASES = (
    "find sources", "summarize articles", "look up",
    "background research", "fact check",
)

_RESEARCH_ONLY_PHRASES = (
    "research only", "just research", "only research",
    "no writing", "without writing",
)


def _normalize_and_tokenize(text: str) -> Tuple[str, frozenset[str]]:
    """
    Normalize text to lowercase and extract tokens.
    
    Returns:
        Tuple of (normalized_string, token_set)
    """
    lowered = text.lower().strip()
    words = _WORD_RE.findall(lowered)
    normalized = " ".join(words)
    tokens = frozenset(words)
    return normalized, tokens


def _infer_intent_rule_based(user_query: str) -> Tuple[str, str, bool]:
    normalized, tokens = _normalize_and_tokenize(user_query)
    has_writing_words = bool(tokens & _WRITING_KEYWORDS)
    has_post_words = bool(tokens & _POST_KEYWORDS)
    has_research_words = bool(tokens & _RESEARCH_KEYWORDS)
    
    has_linkedin = any(phrase in normalized for phrase in _LINKEDIN_PHRASES)
    has_research_phrases = any(phrase in normalized for phrase in _RESEARCH_PHRASES)
    has_research_only = any(phrase in normalized for phrase in _RESEARCH_ONLY_PHRASES)
    
    has_research = has_research_words or has_research_phrases
    has_writing = has_writing_words or has_linkedin
    has_post = has_post_words
    is_writing_intent = has_linkedin or has_writing or has_post
    matched = any([
        has_writing_words, has_post_words, has_research_words,
        has_linkedin, has_research_phrases, has_research_only
    ])
    
    if has_research_only and not is_writing_intent:
        return "research_only", "research_team", matched
    
    if has_linkedin or (has_writing and has_post):
        return "linkedin_post", "writing_team", matched
    
    if has_research and not is_writing_intent:
        return "research_only", "research_team", matched
    
    if has_research and is_writing_intent:
        return "linkedin_post", "writing_team", matched
    
    # No match found
    return "unknown", "none", matched


def _llm_fallback_classifier(user_query: str) -> Tuple[str, str]:
    try:
        llm = get_llm()

        system_prompt = """You are a task classifier for a multi-agent system.

Analyze the user's request and classify it into ONE of these categories:

1. "research_only" - User wants research, information gathering, citations, or sources
   Examples: "find information about X", "what are the latest studies on Y"

2. "linkedin_post" - User wants to create/write content (posts, articles, etc.)
   Examples: "create content about X", "help me share thoughts on Y", "craft a message"

3. "unknown" - Request is unclear or doesn't fit either category
   Examples: "hello", "help", gibberish

Respond with ONLY the category name (research_only, linkedin_post, or unknown).
No explanations, no extra text.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query),
        ]

        response = llm.invoke(messages)

        # Normalize LLM output defensively
        decision = response.content.strip().lower()
        decision = decision.replace("-", "_").replace(" ", "_")

        # Parse LLM response
        if decision.startswith("research"):
            logger.info(f"LLM classified as research: {user_query[:50]}...")
            return "research_only", "research_team"

        if decision.startswith(("linkedin", "writing", "post")):
            logger.info(f"LLM classified as writing: {user_query[:50]}...")
            return "linkedin_post", "writing_team"

        logger.warning(f"LLM returned unknown for: {user_query[:50]}...")
        return "unknown", "none"

    except ImportError:
        logger.error("LLM module not configured. Falling back to 'unknown'.")
        return "unknown", "none"

    except Exception as e:
        logger.error(f"LLM fallback failed: {e}. Returning 'unknown'.")
        return "unknown", "none"

def build_meta_supervisor_state(
    user_query: str,
    use_llm_fallback: bool = True,
) -> MetaSupervisorState:
    # Type validation
    if not isinstance(user_query, str):
        logger.warning("Meta supervisor received non-string user_query: %r", user_query)
        return MetaSupervisorState(user_request="", intent="unknown", target_team="none")
    
    cleaned = user_query.strip()
    if not cleaned:
        return MetaSupervisorState(user_request="", intent="unknown", target_team="none")
    
    intent, team, matched = _infer_intent_rule_based(cleaned)
    
    if not matched and intent == "unknown" and use_llm_fallback:
        logger.info(f"No keyword match found. Using LLM fallback for: {cleaned[:50]}...")
        intent, team = _llm_fallback_classifier(cleaned)
    
    if matched:
        logger.debug(f"Rule-based match: intent={intent}, team={team}")
    else:
        logger.debug(f"LLM fallback used: intent={intent}, team={team}")
    
    return MetaSupervisorState(user_request=cleaned, intent=intent, target_team=team)


def meta_supervisor_node(
    state: AgentState,
    enable_llm_fallback: bool = True
) -> AgentState:
    try:
        user_query: Optional[str] = state.get("user_query", "")
        
        # CONSOLE OUTPUT FOR TESTING
        print(f"🚀 META SUPERVISOR ANALYSIS:")
        print(f"   📝 User Query: {user_query[:100]}...")
        print("-" * 50)
        
        decision = build_meta_supervisor_state(
            user_query or "",
            use_llm_fallback=enable_llm_fallback,
        )
        
        print(f"🎯 INTENT DETECTION RESULTS:")
        print(f"   🎯 Intent: {decision.intent}")
        print(f"   👥 Target Team: {decision.target_team}")
        print(f"   ✅ Classification: {'Rule-based' if decision.intent != 'unknown' or not enable_llm_fallback else 'LLM Fallback'}")
        print("=" * 50)
        
        state["intent"] = decision.intent
        state["target_team"] = decision.target_team
        
        return state
    
    except (KeyError, AttributeError, TypeError) as e:
        logger.error("Meta supervisor node failed with expected error: %s", e, exc_info=True)
        state["intent"] = "unknown"
        state["target_team"] = "none"
        if not state.get("final_output"):
            state["final_output"] = "Sorry, I couldn't process your request due to a system error."
        return state
    
    except Exception:
        logger.exception("Meta supervisor node failed with unexpected error")
        state["intent"] = "unknown"
        state["target_team"] = "none"
        if not state.get("final_output"):
            state["final_output"] = "Sorry, I couldn't process your request due to a system error."
        return state
