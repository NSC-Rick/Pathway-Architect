from typing import Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class ProposalFields(BaseModel):
    """Explicit, closed set of proposal fields supported by the Pathway Architect.

    Using a typed model with extra='forbid' makes the JSON schema compatible with
    OpenAI's strict Structured Outputs. Every field has a concrete type so the
    generated schema contains valid 'type' keys; open-ended 'Any' is avoided.
    """
    model_config = ConfigDict(extra='forbid')

    # Pathway-level fields
    name: Optional[str] = Field(None)
    purpose: Optional[str] = Field(None)
    intended_audience: Optional[str] = Field(None)
    desired_proficiency_outcome: Optional[str] = Field(None)
    draft_status: Optional[str] = Field(None)

    # Stage fields
    stage_id: Optional[str] = Field(None)
    sequence: Optional[int] = Field(None)
    outcome: Optional[str] = Field(None)

    # Milestone fields
    milestone_id: Optional[str] = Field(None)
    title: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    completion_criteria: Optional[str] = Field(None)
    evidence_considered: Optional[str] = Field(None)

    # Evidence fields
    evidence_id: Optional[str] = Field(None)
    evidence_type: Optional[str] = Field(None)
    demonstrated_proficiency: Optional[str] = Field(None)

    # Resource fields
    resource_id: Optional[str] = Field(None)
    resource_type: Optional[str] = Field(None)
    reference: Optional[str] = Field(None)

    # Guardrail fields
    guardrail_id: Optional[str] = Field(None)
    category: Optional[str] = Field(None)
    trigger_conditions: Optional[str] = Field(None)
    escalation_considerations: Optional[str] = Field(None)
    advisor_attention: Optional[Union[str, bool]] = Field(None)

    # Common metadata fields
    sme_notes: Optional[str] = Field(None)
    architect_rationale: Optional[str] = Field(None)


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
