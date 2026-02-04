from typing import List, Optional, Literal
from pydantic import BaseModel

class ResearchExecutionState(BaseModel):
    research_source: Literal["vector", "web"]

    research_query: Optional[str] = None
    raw_documents: Optional[List[str]] = None
    research_summary: Optional[str] = None
    citations: Optional[List[str]] = None
