from assignments.AgenticQASystem3.services.agent_runner import run_agent
from assignments.schemas import ChatRequest
from fastapi import APIRouter
router=APIRouter()
@router.post("/v1/ask")
def ask_agent(request: ChatRequest):
    return run_agent(request.query)