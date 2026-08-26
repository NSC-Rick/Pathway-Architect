from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class Proposal(BaseModel):
    """A single machine-readable proposed Pathway mutation."""
    model_config = ConfigDict(extra='forbid')

    operation: str = Field(..., description="One of the supported mutation operations.")
    target: Optional[str] = Field(None, description="Target identifier (e.g., stage_id, milestone_id, or pathway_id) when relevant.")
    fields: dict[str, Any] = Field(default_factory=dict, description="Fields to set for this operation.")
    reason: Optional[str] = Field(None, description="Architect rationale for this proposal.")


class ArchitectResponse(BaseModel):
    """The structured two-part response the Architect must return."""
    model_config = ConfigDict(extra='forbid')

    message: str = Field(..., description="Natural-language response shown to the SME.")
    proposals: list[Proposal] = Field(default_factory=list, description="Structured Pathway mutation proposals.")
