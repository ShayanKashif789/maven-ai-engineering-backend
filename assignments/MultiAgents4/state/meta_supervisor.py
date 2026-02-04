from typing import Literal, Optional
from pydantic import BaseModel

class MetaSupervisorState(BaseModel):
    user_request: str
    intent: Optional[Literal[
        "linkedin_post",
        "research_only",
        "unknown"
    ]] = None

    target_team: Optional[Literal[
        "research_team",
        "writing_team",
        "none"
    ]] = None
