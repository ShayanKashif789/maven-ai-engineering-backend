import logging
import hashlib
import json

from langchain_core.messages import SystemMessage, HumanMessage

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
        return {"draft_sig": raw}


def _write_notes_meta(state: AgentState, updates: dict) -> None:
    meta = _read_notes_meta(state)
    meta.update(updates)
    state["processing_meta"] = json.dumps(meta, ensure_ascii=True)


def _compute_input_signature(state: AgentState) -> str:
    pieces = [
        state.get("user_query") or "",
        state.get("research_summary") or "",
        state.get("tone") or "",
        str(state.get("writing_plan") or ""),
        state.get("target_format") or "",
        state.get("notes") or "",
    ]
    joined = "\n".join(pieces)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _build_prompt(state: AgentState) -> str:
    user_query = state.get("user_query", "")
    research_summary = state.get("research_summary") or ""
    tone = state.get("tone") or "PROFESSIONAL"
    target_format = state.get("target_format") or "single_post"
    writing_plan = state.get("writing_plan") or {}
    notes_json = state.get("notes") or ""
    post_type = writing_plan.get("post_type") if isinstance(writing_plan, dict) else None
    post_type = post_type or "TECHNICAL_EXPLAINER"

    tone_label = tone.replace("_", " ").lower()
    post_type_label = post_type.replace("_", " ").lower()
    format_label = target_format.replace("_", " ")

    if target_format == "thread":
        length_guidance = "Aim for a short thread (4-8 sections) with a strong hook and clear progression."
    else:
        length_guidance = "Aim for 150-300 words, with short paragraphs (2-3 lines max)."

    if research_summary:
        evidence_rule = "Base claims on the research summary. Do not invent facts."
        research_block = research_summary
    else:
        evidence_rule = "If no research is provided, write as informed opinion and avoid factual claims."
        research_block = "No research summary provided."

    note_guidance = ""
    if notes_json:
        try:
            notes_obj = json.loads(notes_json)
            if isinstance(notes_obj, dict):
                thesis = notes_obj.get("thesis")
                key_points = notes_obj.get("key_points")
                outline = notes_obj.get("outline")
                if thesis:
                    note_guidance += f"- Thesis: {thesis}\n"
                if isinstance(key_points, list) and key_points:
                    note_guidance += "- Key points: " + "; ".join(str(x) for x in key_points[:5]) + "\n"
                if isinstance(outline, list) and outline:
                    note_guidance += "- Outline: " + " -> ".join(str(x) for x in outline[:7]) + "\n"
        except Exception:
            pass

    prompt = f"""You are an expert LinkedIn content writer.

User request:
{user_query}

Research summary:
{research_block}

Post requirements:
- Format: {format_label}
- Tone: {tone_label}
- Post type: {post_type_label}

Guidelines:
- Start with a strong hook in the first 1-2 lines.
- Use line breaks for readability.
- {length_guidance}
- Keep the tone consistent.
- {evidence_rule}
- Do not include hashtags in the main text.
{note_guidance if note_guidance else ""}

Return ONLY the final draft text.
"""
    return prompt


def draft_writer_node(state: AgentState) -> AgentState:
    try:
        if state.get("intent") != "linkedin_post":
            return state

        current_sig = _compute_input_signature(state)
        prev_sig = _read_notes_meta(state).get("draft_sig")
        if state.get("draft") and prev_sig == current_sig:
            return state

        llm = get_llm()
        prompt = _build_prompt(state)
        messages = [
            SystemMessage(content="You are a professional LinkedIn post writer."),
            HumanMessage(content=prompt),
        ]
        response = llm.invoke(messages)
        draft_text = response.content.strip()

        if not draft_text:
            state["draft"] = "Draft unavailable due to an internal error."
            return state

        state["draft"] = draft_text
        _write_notes_meta(state, {"draft_sig": current_sig})
        return state
    except Exception:
        logger.exception("Draft writer failed.")
        if not state.get("final_output"):
            state["final_output"] = "Sorry, I couldn't generate the draft due to a system error."
        return state
