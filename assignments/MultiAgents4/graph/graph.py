import logging
import time
from dataclasses import dataclass
from typing import Callable, List, Optional

from assignments.MultiAgents4.state.agent_state import AgentState
from assignments.MultiAgents4.agents.meta_supervisor import meta_supervisor_node
from assignments.MultiAgents4.agents.Research_supervisor import research_supervisor_node
from assignments.MultiAgents4.agents.research_execution import research_execution_node
from assignments.MultiAgents4.agents.writing_supervisor import writing_supervisor_node
from assignments.MultiAgents4.agents.note_taker import note_taker_node
from assignments.MultiAgents4.agents.draft_writer import draft_writer_node
from assignments.MultiAgents4.agents.draft_editor import draft_editor_node
from assignments.MultiAgents4.agents.finalizer import finalizer_node

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GraphConfig:
    max_retries: int = 1
    backoff_s: float = 0.2
    enable_timing: bool = True
    max_steps: int = 20


@dataclass(frozen=True)
class NodeSpec:
    name: str
    fn: Callable[[AgentState], AgentState]
    condition: Optional[Callable[[AgentState], bool]] = None
    fallback: Optional[Callable[[AgentState], AgentState]] = None
    max_retries: Optional[int] = None


def build_initial_state(user_query: str) -> AgentState:
    return {
        "user_query": user_query,
        "intent": None,
        "target_team": None,
        "research_required": None,
        "research_source": None,
        "research_sources": None,
        "vector_results": None,
        "web_results": None,
        "research_summary": None,
        "research_failed": None,
        "writing_plan": None,
        "target_format": None,
        "tone": None,
        "processing_meta": None,
        "notes": None,
        "draft": None,
        "edited_draft": None,
        "final_output": None,
    }

def _has_value(value: Optional[str]) -> bool:
    return value is not None and value != ""


def _should_run_research_execution(state: AgentState) -> bool:
    if not state.get("research_required"):
        return False
    sources = state.get("research_sources") or []
    if not sources and state.get("research_source") in ("vector", "web"):
        sources = [state["research_source"]]
    if not sources:
        return False
    has_vector = _has_value(state.get("vector_results"))
    has_web = _has_value(state.get("web_results"))
    if ("vector" in sources and not has_vector) or ("web" in sources and not has_web):
        return True
    return False


def _validate_state(state: AgentState) -> bool:
    return _has_value(state.get("user_query"))


def _execute_with_retry(
    spec: NodeSpec,
    state: AgentState,
    config: GraphConfig,
) -> AgentState:
    retries = spec.max_retries if spec.max_retries is not None else config.max_retries
    attempt = 0
    while True:
        try:
            start = time.perf_counter() if config.enable_timing else None
            next_state = spec.fn(state)
            if config.enable_timing and start is not None:
                logger.info("Node %s completed in %.2fms", spec.name, (time.perf_counter() - start) * 1000)
            return next_state
        except Exception:
            attempt += 1
            logger.exception("Node %s failed (attempt %d/%d)", spec.name, attempt, retries + 1)
            if attempt > retries:
                if spec.fallback is not None:
                    return spec.fallback(state)
                return state
            time.sleep(config.backoff_s * attempt)


def run_graph(state: AgentState, config: Optional[GraphConfig] = None) -> AgentState:
    cfg = config or GraphConfig()
    if not _validate_state(state):
        logger.warning("Graph aborted: missing or empty user_query")
        state["final_output"] = "Please provide a query so I can help."
        return state

    nodes: List[NodeSpec] = [
        NodeSpec(name="meta_supervisor", fn=meta_supervisor_node),
        NodeSpec(name="research_supervisor", fn=research_supervisor_node),
        NodeSpec(name="research_execution", fn=research_execution_node, condition=_should_run_research_execution),
        NodeSpec(name="writing_supervisor", fn=writing_supervisor_node),
        NodeSpec(name="note_taker", fn=note_taker_node),
        NodeSpec(name="draft_writer", fn=draft_writer_node),
        NodeSpec(name="draft_editor", fn=draft_editor_node),
        NodeSpec(name="finalizer", fn=finalizer_node),
    ]

    steps = 0
    for spec in nodes:
        if steps >= cfg.max_steps:
            logger.error("Graph aborted: max_steps exceeded")
            break
        if spec.condition is not None and not spec.condition(state):
            continue
        state = _execute_with_retry(spec, state, cfg)
        steps += 1
    return state
