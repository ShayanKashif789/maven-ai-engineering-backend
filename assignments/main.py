import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from assignments.Assignment3.api.routes import router as api_router
from assignments.AgenticQASystem3.api.routes import router as v1_router
from assignments.config import settings
from assignments.Assignment3.core.rag_manager import RAGManager


app = FastAPI(title=settings.PROJECT_NAME)

# Ensure temp directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(v1_router, prefix="/api")
@app.get("/")
def health_check():
    return {"status": "online"}

@app.get("/api/test")
def test():
    return {"message": "Hello World"}