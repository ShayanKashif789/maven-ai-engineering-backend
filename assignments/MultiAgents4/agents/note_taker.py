import hashlib
import json
import logging
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from assignments.AgenticQASystem3.core.llm_factory import get_llm
from assignments.MultiAgents4.state.agent_state import AgentState

logger = logging.getLogger(__name__)
_MIN_SUMMARY_WORDS_FOR_LLM = 30


def _read_processing_meta(state: AgentState) -> Dict[str, Any]:
    raw = state.get("processing_meta")
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_processing_meta(state: AgentState, updates: Dict[str, Any]) -> None:
    meta = _read_processing_meta(state)
    meta.update(updates)
    state["processing_meta"] = json.dumps(meta, ensure_ascii=True)


def _compute_signature(state: AgentState) -> str:
    parts = [
        state.get("user_query") or "",
        state.get("research_summary") or "",
        state.get("tone") or "",
        state.get("target_format") or "",
        str(state.get("writing_plan") or {}),
    ]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _deterministic_notes(state: AgentState) -> Dict[str, Any]:
    user_query = (state.get("user_query") or "").strip()
    research_summary = (state.get("research_summary") or "").strip()
    content = research_summary if research_summary else user_query
    lines = [ln.strip("- ").strip() for ln in content.splitlines() if ln.strip()]

    key_points: List[str] = []
    for ln in lines:
        if len(key_points) >= 5:
            break
        if len(ln) >= 12:
            key_points.append(ln)

    if not key_points and content:
        key_points = [content[:180]]
    while len(key_points) < 3:
        key_points.append("Add one concrete insight tied to the user request.")

    thesis = key_points[0] if key_points else user_query or "Create a focused LinkedIn post."
    outline = ["Hook", "Core insight", "Evidence or example", "Takeaway", "CTA"]
    hooks = [
        f"What most people miss about {user_query[:50]}...",
        f"A practical lesson from {user_query[:50]}:",
    ]

    return {
        "thesis": thesis,
        "key_points": key_points[:5],
        "outline": outline,
        "hook_options": hooks,
        "cta_options": ["What is your take?", "Have you seen similar results?"],
        "risk_flags": [] if research_summary else ["Research summary missing; avoid hard factual claims."],
    }


def _parse_note_json(raw: str) -> Dict[str, Any]:
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return {}
        if not isinstance(data.get("key_points"), list):
            return {}
        if not isinstance(data.get("outline"), list):
            return {}
        return data
    except Exception:
        return {}


def _llm_notes(state: AgentState) -> Dict[str, Any]:
    user_query = state.get("user_query") or ""
    research_summary = state.get("research_summary") or ""
    tone = state.get("tone") or "PROFESSIONAL"
    target_format = state.get("target_format") or "single_post"
    writing_plan = state.get("writing_plan") or {}
    post_type = writing_plan.get("post_type") if isinstance(writing_plan, dict) else "TECHNICAL_EXPLAINER"
    llm = get_llm()
    system = """You are a strategic note taker for LinkedIn content.
Return valid JSON with keys:
thesis (string), key_points (array 3-5 strings), outline (array 4-7 strings),
hook_options (array 2-3 strings), cta_options (array 1-2 strings), risk_flags (array strings).
No markdown. JSON only."""
    human = f"""User query: {user_query}
Research summary: {research_summary}
Tone: {tone}
Target format: {target_format}
Post type: {post_type}
"""
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=human)])
    return _parse_note_json(response.content.strip())


def note_taker_node(state: AgentState, enable_llm_fallback: bool = True) -> AgentState:
    try:
        if state.get("intent") != "linkedin_post":
            return state

        current_sig = _compute_signature(state)
        meta = _read_processing_meta(state)
        if state.get("notes") and meta.get("note_taker_sig") == current_sig:
            return state

        notes_obj = _deterministic_notes(state)
        # Use LLM only for richer synthesis when summary is substantial.
        research_summary = state.get("research_summary") or ""
        if (
            enable_llm_fallback
            and research_summary
            and len(research_summary.split()) >= _MIN_SUMMARY_WORDS_FOR_LLM
        ):
            llm_notes = _llm_notes(state)
            if llm_notes:
                notes_obj = llm_notes

        state["notes"] = json.dumps(notes_obj, ensure_ascii=True)
        _write_processing_meta(state, {"note_taker_sig": current_sig})
        return state
    except Exception:
        logger.exception("Note taker failed.")
        if not state.get("notes"):
            fallback = _deterministic_notes(state)
            state["notes"] = json.dumps(fallback, ensure_ascii=True)
        if not state.get("final_output"):
            state["final_output"] = "Sorry, I couldn't prepare structured notes due to a system error."
        return state
