import os
import shutil

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from assignments.Synthetic_RagSystem5.core.rag_manager import SyntheticRAGManager
from assignments.config import settings
from assignments.schemas import ChatRequest, ChatResponse, UploadResponse
from assignments.Synthetic_RagSystem5.core.evaluation_runner import EvaluationRunner


router = APIRouter(prefix="/synthetic-rag", tags=["Synthetic RAG 5"])
rag = SyntheticRAGManager()
runner = EvaluationRunner(rag)


@router.post("/upload-generate", response_model=UploadResponse)
async def upload_generate(
    file: UploadFile = File(...),
    total_questions: int = Query(default=12, ge=1, le=200),
):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = await rag.process_generate_and_store_evalset(
            file_path=file_path,
            total_questions=total_questions,
        )
        return {
            "status": "success",
            "message": (
                f"Indexed {result['indexed_chunks']} chunks and generated "
                f"{result['generated_qas']} QA records in Qdrant."
            ),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.get("/eval-records")
async def eval_records(
    source_file: str = Query(default=""),
    limit: int = Query(default=50, ge=1, le=500),
):
    try:
        records = await rag.fetch_eval_records(source_file=source_file, limit=limit)
        return {"count": len(records), "records": records}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await rag.aquery(request.query)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(exc)}")
@router.post("/run-evaluation")
async def run_evaluation(limit: int = 20):

    try:
        result = await runner.run_evaluation(limit=limit)
        return result

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))