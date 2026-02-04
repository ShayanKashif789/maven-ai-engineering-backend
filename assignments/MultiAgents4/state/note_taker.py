from typing import List, Optional
from pydantic import BaseModel, Field

from .draft_writer import DraftWriterState

class NoteTakerOutput(BaseModel):
    outline: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    key_takeaways: List[str] = Field(default_factory=list)
    linkedin_hook_options: List[str] = Field(default_factory=list)

class NoteTakerState(BaseModel):
    # Input
    draft_writer_state: DraftWriterState

    # Optional context
    target_audience: Optional[str] = None
    target_tone: Optional[str] = None

    # Output
    output: NoteTakerOutput = Field(default_factory=NoteTakerOutput)
