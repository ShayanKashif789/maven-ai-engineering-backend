from fastapi import APIRouter, HTTPException
from typing import Optional
import logging
import asyncio
from assignments.MultiAgents4.graph.graph import run_graph, build_initial_state, GraphConfig
from assignments.MultiAgents4.state.agent_state import AgentState
from assignments.schemas import MultiAgentRequest, MultiAgentResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/multi-agent", response_model=MultiAgentResponse)
async def trigger_multi_agents(request: MultiAgentRequest):
    """
    Trigger the multi-agent system to process a user query.
    
    This endpoint handles both research-only and content creation requests,
    routing through the appropriate agent pipeline.
    """
    try:
        # Build initial state from user query
        initial_state = build_initial_state(request.query)
        
        # Configure graph options
        config = GraphConfig(
            max_retries=request.max_retries if request.max_retries else 1,
            max_steps=request.max_steps if request.max_steps else 20,
            enable_timing=True
        )
        
        # Run the agent graph
        if request.async_execution:
            # Run asynchronously for better performance
            final_state = await asyncio.to_thread(run_graph, initial_state, config)
        else:
            # Run synchronously
            final_state = run_graph(initial_state, config)
        
        # Extract relevant results
        response = MultiAgentResponse(
            success=True,
            final_output=final_state.get("final_output", ""),
            intent=final_state.get("intent"),
            target_team=final_state.get("target_team"),
            research_required=final_state.get("research_required", False),
            research_source=final_state.get("research_source"),
            tone=final_state.get("tone"),
            target_format=final_state.get("target_format"),
            research_summary=final_state.get("research_summary"),
            draft=final_state.get("draft"),
            edited_draft=final_state.get("edited_draft")
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Multi-agent execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Multi-agent execution failed: {str(e)}"
        )

@router.get("/multi-agent/status")
async def get_system_status():
    """
    Get the current status of the multi-agent system.
    """
    return {
        "status": "online",
        "system": "MultiAgents4",
        "description": "Multi-agent system for research and LinkedIn content creation",
        "capabilities": [
            "Research (vector & web search)",
            "LinkedIn post generation", 
            "Content editing and refinement",
            "Intent classification and routing"
        ]
    }

