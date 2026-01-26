from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
# Notice: We don't need 'from google import genai' here because 
# RAGManager handles the LLM via LangChain internally!
from assignments.Assignment3.core.rag_manager import RAGManager
from assignments.config import settings
from assignments.schemas import ChatRequest, ChatResponse, UploadResponse

router = APIRouter()

# Initialize the manager
rag = RAGManager()

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    # Ensure directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Use the ingestion method from your RAGManager
        num_chunks = rag.process_and_store(file_path)
        os.remove(file_path) 
        return {"status": "success", "message": f"Indexed {num_chunks} chunks."}
    except Exception as e:
        if os.path.exists(file_path): os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await rag.aquery(request.query)

        return result
        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")