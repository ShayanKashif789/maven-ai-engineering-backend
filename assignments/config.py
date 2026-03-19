from pydantic_settings import BaseSettings
from typing import ClassVar
class Settings(BaseSettings):
    PROJECT_NAME: str = "Maven RAG API"
    GROQ_API_KEY: str
    GOOGLE_API_KEY: str
    LLAMA_API_KEY: str = ""
    CHROMA_HOST: str = "chromadb"
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    LLM_MODEL: ClassVar[str] = "llama-3.1-8b-instant"
    LLM_TEMPERATURE:float=0.2
    DEBUG:bool=True
    CHROMA_PORT: int = 8000
    UPLOAD_DIR: str = "/workspace/temp_uploads"
    SERP_API_KEY:str
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
