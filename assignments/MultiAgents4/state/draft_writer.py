from typing import List, Optional
from pydantic import BaseModel, Field

from .writing_supervisor import ResearchInput, WritingPlan

class DraftWriterOutput(BaseModel):
    draft_text: str = ""
    section_headings: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)

class DraftWriterState(BaseModel):
    # Inputs
    research_input: ResearchInput
    writing_plan: WritingPlan

    # Optional context
    topic: Optional[str] = None
    audience: Optional[str] = None
    tone: Optional[str] = None

    # Output
    output: DraftWriterOutput = Field(default_factory=DraftWriterOutput)
