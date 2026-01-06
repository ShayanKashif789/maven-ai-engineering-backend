from pydantic import BaseModel

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: str

class UploadResponse(BaseModel):
    status: str
    message: str