from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
from google import genai
from assignments.Assignment3.core.rag_manager import RAGManager
from assignments.Assignment3.core.config import settings
from assignments.Assignment3.api.schemas import ChatRequest, ChatResponse, UploadResponse

router = APIRouter()
rag = RAGManager()

# Configure Gemini
client = genai.Client(api_key=settings.GOOGLE_API_KEY)

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        num_chunks = rag.process_and_store(file_path)
        os.remove(file_path) # Cleanup
        return {"status": "success", "message": f"Indexed {num_chunks} chunks."}
    except Exception as e:
        if os.path.exists(file_path): os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    context = rag.get_context(request.query)
    prompt = f"Context: {context}\n\nQuestion: {request.query}\nAnswer:"
    
    response = client.models.generate_content(
        model='gemini-2.5-flash', contents=prompt
    )
    return {"answer": response.text, "sources": context}
