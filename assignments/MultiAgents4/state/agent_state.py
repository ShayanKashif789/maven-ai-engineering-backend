from typing import Any, Dict, List, Optional, TypedDict, Literal

class AgentState(TypedDict):
    user_query: str

    # Meta-supervisor outputs
    intent: Optional[Literal["linkedin_post", "research_only", "unknown"]]
    target_team: Optional[Literal["research_team", "writing_team", "none"]]

    # Research supervisor outputs
    research_required: Optional[bool]
    research_source: Optional[Literal["vector", "web", "none"]]
    research_sources: Optional[List[Literal["vector", "web"]]]

    # Research execution
    vector_results: Optional[str]
    web_results: Optional[str]
    research_summary: Optional[str]

    # Writing supervisor outputs
    writing_plan: Optional[Dict[str, Any]]
    target_format: Optional[str]
    tone: Optional[str]

    # Writing pipeline
    processing_meta: Optional[str]
    notes: Optional[str]
    draft: Optional[str]
    edited_draft: Optional[str]
    final_output: Optional[str]
