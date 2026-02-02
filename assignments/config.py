from pydantic_settings import BaseSettings
from typing import ClassVar
class Settings(BaseSettings):
    PROJECT_NAME: str = "Maven RAG API"
    GOOGLE_API_KEY: str
    CHROMA_HOST: str = "chromadb"
    LLM_MODEL: ClassVar[str] = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE:float=0.2
    DEBUG:bool=True
    CHROMA_PORT: int = 8000
    UPLOAD_DIR: str = "/workspace/temp_uploads"
    SERP_API_KEY:str
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
