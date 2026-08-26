"""Server-side validation for Architect structured proposals."""
from models import Stage, Milestone


class ProposalValidationError(Exception):
    """Raised when a proposal fails server-side validation."""


ALLOWED_OPERATIONS = {
    'update_pathway',
    'add_stage',
    'update_stage',
    'add_milestone',
    'update_milestone',
    'add_evidence',
    'add_resource',
    'add_guardrail',
}

ALLOWED_FIELDS = {
    'update_pathway': {
        'name', 'purpose', 'intended_audience', 'desired_proficiency_outcome',
        'sme_notes', 'architect_rationale', 'draft_status',
    },
    'add_stage': {
        'stage_id', 'name', 'sequence', 'purpose', 'outcome', 'sme_notes', 'architect_rationale',
    },
    'update_stage': {
        'name', 'sequence', 'purpose', 'outcome', 'sme_notes', 'architect_rationale',
    },
    'add_milestone': {
        'milestone_id', 'title', 'description', 'completion_criteria', 'evidence_considered',
    },
    'update_milestone': {
        'title', 'description', 'completion_criteria', 'evidence_considered',
    },
    'add_evidence': {
        'evidence_id', 'evidence_type', 'description', 'demonstrated_proficiency',
    },
    'add_resource': {
        'resource_id', 'title', 'resource_type', 'description', 'reference',
    },
    'add_guardrail': {
        'guardrail_id', 'category', 'description', 'trigger_conditions', 'escalation_considerations', 'advisor_attention',
    },
}

REQUIRED_FIELDS = {
    'add_stage': {'name'},
    'add_milestone': {'title'},
    'add_evidence': {'evidence_type', 'description'},
    'add_resource': {'title', 'resource_type'},
    'add_guardrail': {'category', 'description'},
}


def _require_pathway_target(pathway, proposal):
    if proposal.target and proposal.target != pathway.pathway_id:
        raise ProposalValidationError(
            f'update_pathway target must be the current pathway_id; got {proposal.target}'
        )


def _find_stage_by_stage_id(pathway, stage_id):
    for stage in pathway.stages:
        if stage.stage_id == stage_id:
            return stage
    return None


def _find_milestone_by_milestone_id(pathway, milestone_id):
    for milestone in pathway.milestones:
        if milestone.milestone_id == milestone_id:
            return milestone
    return None


def _validate_target_exists(pathway, proposal, required_kind):
    if not proposal.target:
        raise ProposalValidationError(f'{proposal.operation} requires a target {required_kind} identifier.')

    if required_kind == 'stage':
        stage = _find_stage_by_stage_id(pathway, proposal.target)
        if not stage:
            raise ProposalValidationError(f'Stage with stage_id {proposal.target} not found in this Pathway.')
        return stage

    if required_kind == 'milestone':
        milestone = _find_milestone_by_milestone_id(pathway, proposal.target)
        if not milestone:
            raise ProposalValidationError(f'Milestone with milestone_id {proposal.target} not found in this Pathway.')
        return milestone

    raise ProposalValidationError(f'Unknown target requirement: {required_kind}')


def validate_proposal(pathway, proposal):
    """Validate a single proposal against the current Pathway."""
    if proposal.operation not in ALLOWED_OPERATIONS:
        raise ProposalValidationError(f'Unknown operation: {proposal.operation}')

    allowed_fields = ALLOWED_FIELDS.get(proposal.operation, set())
    for key in (proposal.fields_dict):
        if key not in allowed_fields:
            raise ProposalValidationError(
                f'Unsupported field "{key}" for operation {proposal.operation}. Allowed: {sorted(allowed_fields)}'
            )

    required = REQUIRED_FIELDS.get(proposal.operation, set())
    for key in required:
        if key not in (proposal.fields_dict) or not (proposal.fields_dict).get(key):
            raise ProposalValidationError(f'Operation {proposal.operation} requires field "{key}".')

    if proposal.operation == 'update_pathway':
        _require_pathway_target(pathway, proposal)

    elif proposal.operation == 'update_stage':
        _validate_target_exists(pathway, proposal, 'stage')

    elif proposal.operation == 'add_milestone':
        _validate_target_exists(pathway, proposal, 'stage')

    elif proposal.operation == 'add_evidence' and proposal.target:
        _validate_target_exists(pathway, proposal, 'stage')

    elif proposal.operation == 'add_resource' and proposal.target:
        _validate_target_exists(pathway, proposal, 'stage')

    elif proposal.operation == 'update_milestone':
        _validate_target_exists(pathway, proposal, 'milestone')


def validate_proposals(pathway, proposals):
    """Validate a list of proposals. Raise on the first invalid proposal."""
    for proposal in proposals:
        validate_proposal(pathway, proposal)
