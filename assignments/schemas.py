from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: str

class UploadResponse(BaseModel):
    status: str
    message: str

class MultiAgentRequest(BaseModel):
    query: str
    async_execution: Optional[bool] = False
    max_retries: Optional[int] = None
    max_steps: Optional[int] = None

class MultiAgentResponse(BaseModel):
    success: bool
    final_output: str
    intent: Optional[str] = None
    target_team: Optional[str] = None
    research_required: Optional[bool] = None
    research_source: Optional[str] = None
    tone: Optional[str] = None
    target_format: Optional[str] = None
    research_summary: Optional[str] = None
    draft: Optional[str] = None
    edited_draft: Optional[str] = None