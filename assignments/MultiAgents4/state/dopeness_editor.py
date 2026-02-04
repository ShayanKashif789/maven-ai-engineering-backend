from typing import List
from pydantic import BaseModel, Field

class DopenessEditorOutput(BaseModel):
    dope_text: str = ""
    emojis_used: List[str] = Field(default_factory=list)
    style_notes: List[str] = Field(default_factory=list)

class DopenessEditorState(BaseModel):
    # Input
    final_response: str

    # Output
    output: DopenessEditorOutput = Field(default_factory=DopenessEditorOutput)
