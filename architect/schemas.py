from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ProposalFields(BaseModel):
    """Explicit, closed set of proposal fields supported by the Pathway Architect.

    Using a typed model with extra='forbid' makes the JSON schema compatible with
    OpenAI's strict Structured Outputs, which requires 'additionalProperties' to
    be supplied and false for every object.
    """
    model_config = ConfigDict(extra='forbid')

    # Pathway-level fields
    name: Optional[Any] = Field(None)
    purpose: Optional[Any] = Field(None)
    intended_audience: Optional[Any] = Field(None)
    desired_proficiency_outcome: Optional[Any] = Field(None)
    draft_status: Optional[Any] = Field(None)

    # Stage fields
    stage_id: Optional[Any] = Field(None)
    sequence: Optional[Any] = Field(None)
    outcome: Optional[Any] = Field(None)

    # Milestone fields
    milestone_id: Optional[Any] = Field(None)
    title: Optional[Any] = Field(None)
    description: Optional[Any] = Field(None)
    completion_criteria: Optional[Any] = Field(None)
    evidence_considered: Optional[Any] = Field(None)

    # Evidence fields
    evidence_id: Optional[Any] = Field(None)
    evidence_type: Optional[Any] = Field(None)
    demonstrated_proficiency: Optional[Any] = Field(None)

    # Resource fields
    resource_id: Optional[Any] = Field(None)
    resource_type: Optional[Any] = Field(None)
    reference: Optional[Any] = Field(None)

    # Guardrail fields
    guardrail_id: Optional[Any] = Field(None)
    category: Optional[Any] = Field(None)
    trigger_conditions: Optional[Any] = Field(None)
    escalation_considerations: Optional[Any] = Field(None)
    advisor_attention: Optional[Any] = Field(None)

    # Common metadata fields
    sme_notes: Optional[Any] = Field(None)
    architect_rationale: Optional[Any] = Field(None)


class Proposal(BaseModel):
    """A single machine-readable proposed Pathway mutation."""
    model_config = ConfigDict(extra='forbid')

    operation: str = Field(..., description="One of the supported mutation operations.")
    target: Optional[str] = Field(None, description="Target identifier (e.g., stage_id, milestone_id, or pathway_id) when relevant.")
    fields: ProposalFields = Field(default_factory=ProposalFields, description="Fields to set for this operation.")
    reason: Optional[str] = Field(None, description="Architect rationale for this proposal.")

    @property
    def fields_dict(self) -> dict:
        """Return the proposal fields as a plain dict, dropping unset None values."""
        return self.fields.model_dump(exclude_none=True)


class ArchitectResponse(BaseModel):
    """The structured two-part response the Architect must return."""
    model_config = ConfigDict(extra='forbid')

    message: str = Field(..., description="Natural-language response shown to the SME.")
    proposals: list[Proposal] = Field(default_factory=list, description="Structured Pathway mutation proposals.")
