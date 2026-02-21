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
    max_retries: Optional[int] = None
    max_steps: Optional[int] = None
    async_execution: bool = True

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
    vector_results: Optional[str] = None
    web_results: Optional[str] = None