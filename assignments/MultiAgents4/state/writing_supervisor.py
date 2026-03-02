from typing import Optional, Literal
from pydantic import BaseModel, Field, PrivateAttr

class ResearchInput(BaseModel):
    summary: list[str] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)

    model_config = {"validate_assignment": True}  
class WritingPlan(BaseModel):
    post_type: Literal['TECHNICAL_EXPLAINER', 'STORY_DRIVEN', 'OPINION_HOT_TAKE', 'ANNOUNCEMENT', 'EDUCATIONAL_THREAD'] = 'TECHNICAL_EXPLAINER'
    required_agents: list[str] = Field(default_factory=list)
    execution_order: list[str] = Field(default_factory=list)

class IntermediateOutputs(BaseModel):
    draft: Optional[str] = None
    edited_draft: Optional[str] = None
    polished_draft: Optional[str] = None

class FinalOutput(BaseModel):
    post_text: str = ""
    hashtags: list[str] = Field(default_factory=list)
    call_to_action: str = ""

class QualityChecks(BaseModel):
    tone_match: bool = False
    constraint_violations: list[str] = Field(default_factory=list)

class Status(BaseModel):
    current_agent: Optional[str] = None
    completed_agents: list[str] = Field(default_factory=list)
    is_complete: bool = False

# --------------------------
# Main WritingState Model
# --------------------------
class WritingState(BaseModel):
    # User Intent
    topic: str = ""
    audience: str = ""
    tone: Literal['PROFESSIONAL', 'CONVERSATIONAL', 'OPINIONATED', 'STORYTELLING', 'EDUCATIONAL', 'THREATENING'] = 'PROFESSIONAL'
    post_goal: str = ""

    # Research Input (read-only)
    research_input: ResearchInput = Field(default_factory=ResearchInput)

    # Supervisor Decisions
    writing_plan: WritingPlan = Field(default_factory=WritingPlan)

    # Agent Outputs
    intermediate_outputs: IntermediateOutputs = Field(default_factory=IntermediateOutputs)

    # Final Output
    final_output: FinalOutput = Field(default_factory=FinalOutput)

    # Quality Checks
    quality_checks: QualityChecks = Field(default_factory=QualityChecks)

    # Execution Tracking
    status: Status = Field(default_factory=Status)

    model_config = {"arbitrary_types_allowed": True}
