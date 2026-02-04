from typing import Literal, Optional
from pydantic import BaseModel

class ResearchSupervisorState(BaseModel):
    user_request: str
    intent: Literal[
        "linkedin_post",
        "research_only",
        "unknown"
    ]
    research_required: Optional[bool] = None

    research_source: Optional[Literal[
        "vector",
        "web",
        "none"
    ]] = None
