from typing import List, Optional
from pydantic import BaseModel, Field

from .draft_writer import DraftWriterState

class DraftEditorOutput(BaseModel):
    edited_text: str = ""
    grammar_fixes: List[str] = Field(default_factory=list)
    readability_improvements: List[str] = Field(default_factory=list)
    flow_improvements: List[str] = Field(default_factory=list)
    tone_alignment_issues: List[str] = Field(default_factory=list)

class DraftEditorState(BaseModel):
    # Input
    draft_writer_state: DraftWriterState

    # Optional context
    target_tone: Optional[str] = None

    # Output
    output: DraftEditorOutput = Field(default_factory=DraftEditorOutput)
