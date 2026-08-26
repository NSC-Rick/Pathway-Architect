"""Deterministic Pathway context builder for the AI Pathway Architect."""


def build_pathway_context(pathway):
    """Return an explicit, testable serialization of the current Pathway state."""
    stages = []
    for stage in pathway.stages:
        stages.append({
            "id": stage.id,
            "stage_id": stage.stage_id,
            "name": stage.name,
            "sequence": stage.sequence,
            "purpose": stage.purpose,
            "outcome": stage.outcome,
            "sme_notes": stage.sme_notes,
            "architect_rationale": stage.architect_rationale,
            "milestones": [
                {
                    "id": m.id,
                    "milestone_id": m.milestone_id,
                    "title": m.title,
                    "description": m.description,
                    "completion_criteria": m.completion_criteria,
                    "evidence_considered": m.evidence_considered,
                }
                for m in stage.milestones
            ],
            "evidence": [
                {
                    "id": e.id,
                    "evidence_id": e.evidence_id,
                    "evidence_type": e.evidence_type,
                    "description": e.description,
                    "demonstrated_proficiency": e.demonstrated_proficiency,
                }
                for e in stage.evidence_items
            ],
            "resources": [
                {
                    "id": r.id,
                    "resource_id": r.resource_id,
                    "title": r.title,
                    "resource_type": r.resource_type,
                    "description": r.description,
                    "reference": r.reference,
                }
                for r in stage.resources
            ],
        })

    return {
        "information_domain": pathway.information_domain.name if pathway.information_domain else None,
        "pathway_id": pathway.pathway_id,
        "name": pathway.name,
        "version": pathway.version,
        "status": pathway.status,
        "draft_status": pathway.draft_status,
        "purpose": pathway.purpose,
        "intended_audience": pathway.intended_audience,
        "desired_proficiency_outcome": pathway.desired_proficiency_outcome,
        "sme_notes": pathway.sme_notes,
        "architect_rationale": pathway.architect_rationale,
        "stages": stages,
        "milestones": [
            {
                "id": m.id,
                "milestone_id": m.milestone_id,
                "stage_id": m.stage_id,
                "title": m.title,
                "description": m.description,
                "completion_criteria": m.completion_criteria,
                "evidence_considered": m.evidence_considered,
            }
            for m in pathway.milestones
        ],
        "evidence_items": [
            {
                "id": e.id,
                "evidence_id": e.evidence_id,
                "stage_id": e.stage_id,
                "milestone_id": e.milestone_id,
                "evidence_type": e.evidence_type,
                "description": e.description,
                "demonstrated_proficiency": e.demonstrated_proficiency,
            }
            for e in pathway.evidence_items
        ],
        "resources": [
            {
                "id": r.id,
                "resource_id": r.resource_id,
                "stage_id": r.stage_id,
                "milestone_id": r.milestone_id,
                "title": r.title,
                "resource_type": r.resource_type,
                "description": r.description,
                "reference": r.reference,
            }
            for r in pathway.resources
        ],
        "guardrails": [
            {
                "id": g.id,
                "guardrail_id": g.guardrail_id,
                "category": g.category,
                "description": g.description,
                "trigger_conditions": g.trigger_conditions,
                "escalation_considerations": g.escalation_considerations,
                "advisor_attention": g.advisor_attention,
            }
            for g in pathway.guardrails
        ],
    }
