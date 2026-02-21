from assignments.MultiAgents4.state.agent_state import AgentState


def finalizer_node(state: AgentState) -> AgentState:
    # Preserve any explicit error/fallback output set by upstream nodes.
    if state.get("final_output"):
        return state

    intent = state.get("intent")
    if intent == "research_only":
        state["final_output"] = state.get("research_summary") or "No research results available."
        return state

    if intent == "linkedin_post":
        state["final_output"] = (
            state.get("edited_draft")
            or state.get("draft")
            or "Sorry, I couldn't generate the requested post."
        )
        return state

    state["final_output"] = "Please share more details so I can help."
    return state
