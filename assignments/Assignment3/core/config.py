from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Maven RAG API"
    GOOGLE_API_KEY: str
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000
    UPLOAD_DIR: str = "/workspace/temp_uploads"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
