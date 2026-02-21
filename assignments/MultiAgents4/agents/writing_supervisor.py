import logging
import re
from typing import Optional, Tuple

from langchain_core.messages import SystemMessage, HumanMessage

from assignments.AgenticQASystem3.core.llm_factory import get_llm
from assignments.MultiAgents4.state.agent_state import AgentState
from assignments.MultiAgents4.state.writing_supervisor import WritingPlan

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"[a-z0-9']+")

_TONE_KEYWORDS = {
    "professional": "PROFESSIONAL",
    "formal": "PROFESSIONAL",
    "casual": "CONVERSATIONAL",
    "conversational": "CONVERSATIONAL",
    "opinionated": "OPINIONATED",
    "hot take": "OPINIONATED",
    "story": "STORYTELLING",
    "storytelling": "STORYTELLING",
    "educational": "EDUCATIONAL",
    "teach": "EDUCATIONAL",
    "explainer": "EDUCATIONAL",
}

_POST_TYPE_KEYWORDS = {
    "thread": "EDUCATIONAL_THREAD",
    "carousel": "EDUCATIONAL_THREAD",
    "announcement": "ANNOUNCEMENT",
    "story": "STORY_DRIVEN",
    "opinion": "OPINION_HOT_TAKE",
    "hot take": "OPINION_HOT_TAKE",
    "technical": "TECHNICAL_EXPLAINER",
    "explainer": "TECHNICAL_EXPLAINER",
}

_CONFIDENCE_THRESHOLD = 0.55
_STRONG_SIGNAL_THRESHOLD = 0.75
_MIN_SUMMARY_WORDS = 5

_VALID_TONES = {
    "PROFESSIONAL",
    "CONVERSATIONAL",
    "OPINIONATED",
    "STORYTELLING",
    "EDUCATIONAL",
}

_VALID_POST_TYPES = {
    "TECHNICAL_EXPLAINER",
    "STORY_DRIVEN",
    "OPINION_HOT_TAKE",
    "ANNOUNCEMENT",
    "EDUCATIONAL_THREAD",
}

_VALID_TARGET_FORMATS = {"single_post", "thread"}


def _normalize(text: str) -> str:
    return " ".join(_WORD_RE.findall(text.lower().strip()))


def _score_signals(text: str) -> Tuple[str, str, float, int, int]:
    normalized = _normalize(text)
    tone_scores = {
        "PROFESSIONAL": 0.0,
        "CONVERSATIONAL": 0.0,
        "OPINIONATED": 0.0,
        "STORYTELLING": 0.0,
        "EDUCATIONAL": 0.0,
    }
    post_scores = {
        "TECHNICAL_EXPLAINER": 0.0,
        "STORY_DRIVEN": 0.0,
        "OPINION_HOT_TAKE": 0.0,
        "ANNOUNCEMENT": 0.0,
        "EDUCATIONAL_THREAD": 0.0,
    }

    for phrase, tone in _TONE_KEYWORDS.items():
        if phrase in normalized:
            tone_scores[tone] += 1.0 if " " in phrase else 0.6

    for phrase, post_type in _POST_TYPE_KEYWORDS.items():
        if phrase in normalized:
            post_scores[post_type] += 1.0 if " " in phrase else 0.6

    tone = max(tone_scores, key=tone_scores.get)
    post_type = max(post_scores, key=post_scores.get)

    tone_strength = tone_scores[tone]
    post_strength = post_scores[post_type]
    combined = (tone_strength + post_strength) / 2.0

    # Normalize into 0..1 range with diminishing returns
    confidence = min(combined / 1.4, 1.0)

    tone_nonzero = sum(1 for v in tone_scores.values() if v > 0)
    post_nonzero = sum(1 for v in post_scores.values() if v > 0)
    if tone_nonzero > 1:
        confidence *= 0.7
    if post_nonzero > 1:
        confidence *= 0.7

    return tone, post_type, confidence, tone_nonzero, post_nonzero


def _llm_fallback_writer_classifier(user_query: str) -> Tuple[str, str, str]:
    try:
        llm = get_llm()
        system_prompt = """You are a writing planner for LinkedIn posts.
Return a JSON object with keys: tone, post_type, target_format.
Valid tones: PROFESSIONAL, CONVERSATIONAL, OPINIONATED, STORYTELLING, EDUCATIONAL.
Valid post_type: TECHNICAL_EXPLAINER, STORY_DRIVEN, OPINION_HOT_TAKE, ANNOUNCEMENT, EDUCATIONAL_THREAD.
Valid target_format: single_post, thread.
Return ONLY JSON, no extra text.
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query),
        ]
        response = llm.invoke(messages).content.strip()
        # Defensive parsing without external deps
        if response.startswith("{") and response.endswith("}"):
            import json
            data = json.loads(response)
            tone = data.get("tone") or "PROFESSIONAL"
            post_type = data.get("post_type") or "TECHNICAL_EXPLAINER"
            target_format = data.get("target_format") or "single_post"
            if tone not in _VALID_TONES:
                tone = "PROFESSIONAL"
            if post_type not in _VALID_POST_TYPES:
                post_type = "TECHNICAL_EXPLAINER"
            if target_format not in _VALID_TARGET_FORMATS:
                target_format = "single_post"
            return tone, post_type, target_format
        return "PROFESSIONAL", "TECHNICAL_EXPLAINER", "single_post"
    except Exception:
        logger.exception("LLM fallback for writing planner failed.")
        return "PROFESSIONAL", "TECHNICAL_EXPLAINER", "single_post"


def writing_supervisor_node(state: AgentState, enable_llm_fallback: bool = True) -> AgentState:
    try:
        intent = state.get("intent")
        if intent != "linkedin_post":
            return state

        user_query = state.get("user_query", "")
        research_summary = state.get("research_summary") or ""

        # Prefer research summary only if it is sufficiently informative
        if research_summary and len(research_summary.split()) >= _MIN_SUMMARY_WORDS:
            source_text = research_summary
        else:
            source_text = user_query

        tone, post_type, confidence, tone_nonzero, post_nonzero = _score_signals(source_text)
        target_format = "thread" if post_type == "EDUCATIONAL_THREAD" else "single_post"

        # Low-confidence -> LLM fallback
        if enable_llm_fallback and confidence < _CONFIDENCE_THRESHOLD:
            fallback_input = research_summary if research_summary else user_query
            tone, post_type, target_format = _llm_fallback_writer_classifier(fallback_input)
        elif confidence >= _STRONG_SIGNAL_THRESHOLD:
            logger.debug(
                "Writing supervisor high confidence: %.2f (tone signals=%d, post signals=%d)",
                confidence,
                tone_nonzero,
                post_nonzero,
            )

        if tone not in _VALID_TONES:
            tone = "PROFESSIONAL"
        if post_type not in _VALID_POST_TYPES:
            post_type = "TECHNICAL_EXPLAINER"
        if target_format not in _VALID_TARGET_FORMATS:
            target_format = "single_post"

        state["tone"] = tone
        state["target_format"] = target_format
        state["writing_plan"] = WritingPlan(
            post_type=post_type,
            required_agents=["draft_writer", "draft_editor"],
            execution_order=["draft_writer", "draft_editor"],
        ).model_dump()
        return state
    except Exception:
        logger.exception("Writing supervisor failed.")
        if not state.get("final_output"):
            state["final_output"] = "Sorry, I couldn't process your request due to a system error."
        return state
