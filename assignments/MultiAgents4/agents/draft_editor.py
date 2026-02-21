import hashlib
import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from assignments.AgenticQASystem3.core.llm_factory import get_llm
from assignments.MultiAgents4.state.agent_state import AgentState

logger = logging.getLogger(__name__)


def _read_notes_meta(state: AgentState) -> dict:
    raw = state.get("processing_meta")
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        # Backward compatibility with previous plain-string notes.
        return {"draft_sig": raw}


def _write_notes_meta(state: AgentState, updates: dict) -> None:
    meta = _read_notes_meta(state)
    meta.update(updates)
    state["processing_meta"] = json.dumps(meta, ensure_ascii=True)


def _compute_editor_signature(state: AgentState) -> str:
    pieces = [
        state.get("draft") or "",
        state.get("tone") or "",
        state.get("target_format") or "",
        str(state.get("writing_plan") or ""),
        state.get("research_summary") or "",
    ]
    joined = "\n".join(pieces)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _build_editor_prompt(state: AgentState) -> str:
    draft = state.get("draft") or ""
    tone = (state.get("tone") or "PROFESSIONAL").replace("_", " ").lower()
    target_format = (state.get("target_format") or "single_post").replace("_", " ")
    research_summary = state.get("research_summary") or "No research summary provided."
    writing_plan = state.get("writing_plan") or {}
    post_type = writing_plan.get("post_type") if isinstance(writing_plan, dict) else "TECHNICAL_EXPLAINER"
    post_type = (post_type or "TECHNICAL_EXPLAINER").replace("_", " ").lower()

    return f"""Edit the LinkedIn draft below.

Current draft:
{draft}

Constraints:
- Tone: {tone}
- Format: {target_format}
- Post type: {post_type}
- Research summary: {research_summary}

Editing goals:
- Keep the same core meaning and scope.
- Improve clarity, flow, and readability.
- Keep short, scannable paragraphs.
- Remove unsupported claims if not grounded in the research summary.
- Keep engagement quality high (hook + clear takeaway).
- Do not add hashtags in main body text.

Return ONLY the edited draft text.
"""


def draft_editor_node(state: AgentState) -> AgentState:
    try:
        if state.get("intent") != "linkedin_post":
            return state
        if not state.get("draft"):
            return state

        current_sig = _compute_editor_signature(state)
        notes_meta = _read_notes_meta(state)
        if state.get("edited_draft") and notes_meta.get("editor_sig") == current_sig:
            return state

        llm = get_llm()
        messages = [
            SystemMessage(content="You are a precise LinkedIn editor. Improve quality without changing meaning."),
            HumanMessage(content=_build_editor_prompt(state)),
        ]
        response = llm.invoke(messages)
        edited = response.content.strip()

        if not edited:
            state["edited_draft"] = state.get("draft")
            _write_notes_meta(state, {"editor_sig": current_sig})
            return state

        state["edited_draft"] = edited
        state["final_output"] = edited
        _write_notes_meta(state, {"editor_sig": current_sig})
        return state
    except Exception:
        logger.exception("Draft editor failed.")
        # Fallback: preserve already generated content.
        if state.get("draft") and not state.get("edited_draft"):
            state["edited_draft"] = state.get("draft")
        if state.get("edited_draft") and not state.get("final_output"):
            state["final_output"] = state.get("edited_draft")
        if not state.get("final_output"):
            state["final_output"] = "Sorry, I couldn't polish your draft due to a system error."
        return state
