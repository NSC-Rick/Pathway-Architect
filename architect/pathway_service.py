"""Apply validated Architect proposals to Pathway models and manage conversation persistence."""
from datetime import datetime

from models import (
    db,
    ArchitectConversation,
    ArchitectMessage,
    Pathway,
    Stage,
    Milestone,
    Evidence,
    Resource,
    Guardrail,
)
from .ai_service import generate_architect_response, ArchitectAIError
from .prompts import OPENING_MESSAGE
from .schemas import ArchitectResponse, Proposal
from .validation import validate_proposal, ProposalValidationError


class PathwayServiceError(Exception):
    """Raised when a Pathway service operation cannot complete."""


def _next_sequence(items, key):
    if not items:
        return 1
    return max(getattr(i, key) for i in items) + 1


def _generate_id(prefix, existing, key):
    n = 1
    existing_ids = {getattr(i, key) for i in existing}
    while f'{prefix}-{n:02d}' in existing_ids:
        n += 1
    return f'{prefix}-{n:02d}'


def get_or_create_conversation(pathway, user):
    """Get the active ArchitectConversation for a pathway/user or create one."""
    conversation = ArchitectConversation.query.filter_by(
        pathway_id=pathway.id, user_id=user.id, status='active'
    ).order_by(ArchitectConversation.created_at.desc()).first()

    if conversation:
        return conversation

    conversation = ArchitectConversation(
        pathway_id=pathway.id,
        user_id=user.id,
        status='active',
    )
    db.session.add(conversation)
    db.session.flush()

    # Open the conversation with a domain-appropriate discovery question.
    opening = ArchitectMessage(
        conversation_id=conversation.id,
        role='architect',
        content=OPENING_MESSAGE,
    )
    db.session.add(opening)

    return conversation


def _add_user_message(conversation, content):
    message = ArchitectMessage(
        conversation_id=conversation.id,
        role='user',
        content=content,
    )
    db.session.add(message)
    return message


def _add_architect_message(conversation, content):
    message = ArchitectMessage(
        conversation_id=conversation.id,
        role='architect',
        content=content,
    )
    db.session.add(message)
    return message


def _apply_update_pathway(pathway, proposal):
    for key, value in proposal.fields.items():
        if hasattr(pathway, key):
            setattr(pathway, key, value)
    if proposal.reason:
        existing = (pathway.architect_rationale or '').strip()
        if existing:
            pathway.architect_rationale = existing + '\n\n' + proposal.reason
        else:
            pathway.architect_rationale = proposal.reason


def _apply_add_stage(pathway, proposal):
    fields = proposal.fields or {}
    stage_id = fields.get('stage_id') or _generate_id('STG', pathway.stages, 'stage_id')
    sequence = fields.get('sequence')
    if sequence is None:
        sequence = _next_sequence(pathway.stages, 'sequence')
    stage = Stage(
        pathway_id=pathway.id,
        stage_id=stage_id,
        name=fields['name'],
        sequence=sequence,
        purpose=fields.get('purpose'),
        outcome=fields.get('outcome'),
        sme_notes=fields.get('sme_notes'),
        architect_rationale=proposal.reason,
    )
    db.session.add(stage)


def _apply_update_stage(pathway, proposal):
    from .validation import _find_stage_by_stage_id
    stage = _find_stage_by_stage_id(pathway, proposal.target)
    if not stage:
        raise PathwayServiceError(f'Stage {proposal.target} not found.')
    for key, value in proposal.fields.items():
        if hasattr(stage, key):
            setattr(stage, key, value)
    if proposal.reason:
        existing = (stage.architect_rationale or '').strip()
        if existing:
            stage.architect_rationale = existing + '\n\n' + proposal.reason
        else:
            stage.architect_rationale = proposal.reason


def _apply_add_milestone(pathway, proposal):
    from .validation import _find_stage_by_stage_id
    stage = _find_stage_by_stage_id(pathway, proposal.target)
    if not stage:
        raise PathwayServiceError(f'Stage {proposal.target} not found for add_milestone.')
    fields = proposal.fields or {}
    milestone_id = fields.get('milestone_id') or _generate_id('MIL', pathway.milestones, 'milestone_id')
    milestone = Milestone(
        pathway_id=pathway.id,
        stage_id=stage.id,
        milestone_id=milestone_id,
        title=fields['title'],
        description=fields.get('description'),
        completion_criteria=fields.get('completion_criteria'),
        evidence_considered=fields.get('evidence_considered'),
    )
    db.session.add(milestone)


def _apply_update_milestone(pathway, proposal):
    from .validation import _find_milestone_by_milestone_id
    milestone = _find_milestone_by_milestone_id(pathway, proposal.target)
    if not milestone:
        raise PathwayServiceError(f'Milestone {proposal.target} not found.')
    for key, value in proposal.fields.items():
        if hasattr(milestone, key):
            setattr(milestone, key, value)


def _apply_add_evidence(pathway, proposal):
    from .validation import _find_stage_by_stage_id
    fields = proposal.fields or {}
    stage_id = None
    stage = None
    if proposal.target:
        stage = _find_stage_by_stage_id(pathway, proposal.target)
        if stage:
            stage_id = stage.id
    evidence_id = fields.get('evidence_id') or _generate_id('EVI', pathway.evidence_items, 'evidence_id')
    evidence = Evidence(
        pathway_id=pathway.id,
        stage_id=stage_id,
        evidence_id=evidence_id,
        evidence_type=fields['evidence_type'],
        description=fields['description'],
        demonstrated_proficiency=fields.get('demonstrated_proficiency'),
    )
    db.session.add(evidence)


def _apply_add_resource(pathway, proposal):
    from .validation import _find_stage_by_stage_id
    fields = proposal.fields or {}
    stage_id = None
    stage = None
    if proposal.target:
        stage = _find_stage_by_stage_id(pathway, proposal.target)
        if stage:
            stage_id = stage.id
    resource_id = fields.get('resource_id') or _generate_id('RES', pathway.resources, 'resource_id')
    resource = Resource(
        pathway_id=pathway.id,
        stage_id=stage_id,
        resource_id=resource_id,
        title=fields['title'],
        resource_type=fields['resource_type'],
        description=fields.get('description'),
        reference=fields.get('reference'),
    )
    db.session.add(resource)


def _apply_add_guardrail(pathway, proposal):
    fields = proposal.fields or {}
    guardrail_id = fields.get('guardrail_id') or _generate_id('GUA', pathway.guardrails, 'guardrail_id')
    advisor_attention = fields.get('advisor_attention', False)
    if isinstance(advisor_attention, str):
        advisor_attention = advisor_attention.lower() in ('true', '1', 'yes')
    guardrail = Guardrail(
        pathway_id=pathway.id,
        guardrail_id=guardrail_id,
        category=fields['category'],
        description=fields['description'],
        trigger_conditions=fields.get('trigger_conditions'),
        escalation_considerations=fields.get('escalation_considerations'),
        advisor_attention=bool(advisor_attention),
    )
    db.session.add(guardrail)


_APPLY_DISPATCH = {
    'update_pathway': _apply_update_pathway,
    'add_stage': _apply_add_stage,
    'update_stage': _apply_update_stage,
    'add_milestone': _apply_add_milestone,
    'update_milestone': _apply_update_milestone,
    'add_evidence': _apply_add_evidence,
    'add_resource': _apply_add_resource,
    'add_guardrail': _apply_add_guardrail,
}


def _apply_proposals(pathway, proposals):
    """Apply a validated list of proposals to the Pathway."""
    for proposal in proposals:
        _APPLY_DISPATCH[proposal.operation](pathway, proposal)


def _validate_ownership(pathway, user):
    if user.role == 'ADMIN' or pathway.user_id == user.id:
        return
    raise PathwayServiceError('User is not authorized to modify this Pathway.')


def process_architect_turn(pathway, user, user_content):
    """Run one Architect turn: persist the SME message, call the AI, then save the Architect response and proposals.

    The SME message is committed before the AI call so that it is preserved even if
    the AI fails. The Pathway is NOT altered here. Proposals are returned to the
    caller (the workspace) so the SME can review and approve or reject each one.
    """
    # Ensure the Pathway and User are bound to the current session.
    pathway = db.session.merge(pathway)
    user = db.session.merge(user)

    _validate_ownership(pathway, user)

    conversation = None
    try:
        # First, persist the SME message in its own savepoint/transaction so it
        # survives an AI failure.
        with db.session.begin_nested():
            conversation = get_or_create_conversation(pathway, user)
            _add_user_message(conversation, user_content)
        db.session.commit()

        prior_messages = ArchitectMessage.query.filter_by(
            conversation_id=conversation.id
        ).order_by(ArchitectMessage.created_at).all()

        # Remove the just-added user message from the prompt list to avoid a duplicate.
        prompt_messages = [m for m in prior_messages if m.role != 'user' or m.content != user_content]

        ai_response = generate_architect_response(pathway, prompt_messages, user_content)

        # Save the Architect's conversational response.
        with db.session.begin_nested():
            _add_architect_message(conversation, ai_response.message)

            # Update draft status to reflect active Architect engagement.
            if pathway.draft_status in ('new', 'saved'):
                pathway.draft_status = 'interviewing'

        db.session.commit()
        return ai_response
    except ArchitectAIError as e:
        # Convert expected AI errors into a single, safe service-level error.
        # The SME message is already committed and will not be lost.
        raise PathwayServiceError('Architect could not generate a response.') from e
    except Exception as e:
        # Wrap unexpected errors without exposing sensitive details.
        raise PathwayServiceError('Architect turn failed.') from e


def apply_architect_proposal(pathway, user, proposal):
    """Apply a single SME-approved Architect proposal to the Pathway."""
    pathway = db.session.merge(pathway)
    user = db.session.merge(user)

    _validate_ownership(pathway, user)

    try:
        with db.session.begin_nested():
            validate_proposal(pathway, proposal)
            _APPLY_DISPATCH[proposal.operation](pathway, proposal)

        db.session.commit()
    except ProposalValidationError as e:
        raise PathwayServiceError(str(e)) from e
    except Exception as e:
        raise PathwayServiceError(f'Could not apply proposal: {e}') from e
