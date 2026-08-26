# PA-003 Architect Response Contract

This document defines the structured two-part response contract and human-in-the-loop approval flow used by the AI Pathway Architect in PA-003.

## Response schema

The Architect must return a JSON object matching the `ArchitectResponse` Pydantic model:

```json
{
  "message": "Natural-language response shown to the SME, usually including one focused question.",
  "proposals": [
    {
      "operation": "update_pathway | add_stage | update_stage | add_milestone | update_milestone | add_evidence | add_resource | add_guardrail",
      "target": "identifier when relevant (e.g., stage_id, milestone_id, or pathway_id)",
      "fields": { "field_name": "value" },
      "reason": "Architect rationale for this proposal."
    }
  ]
}
```

`proposals` may be an empty list if the Architect is only asking a question. The SME must explicitly approve every proposal before it is written to the Pathway.

## Human-in-the-loop rule

- **AI PROPOSES.**
- **SME DECIDES.**
- **DATABASE RECORDS THE APPROVED STATE.**

The Architect service never mutates the authoritative Pathway directly. It only returns `proposals`. The application renders those proposals in the workspace. The SME can choose **Apply Suggestion** or **Keep Current and Continue**. Only after the SME clicks **Apply Suggestion** does the server validate and apply the proposal.

## Supported mutation operations

| Operation | Target | Allowed fields | Effect |
|---|---|---|---|
| `update_pathway` | `pathway_id` or omitted | `name`, `purpose`, `intended_audience`, `desired_proficiency_outcome`, `sme_notes`, `architect_rationale` | Update top-level Pathway fields. **Priority focus for PA-003.** |
| `add_stage` | omitted | `stage_id`, `name`, `sequence`, `purpose`, `outcome`, `sme_notes`, `architect_rationale` | Create a new Stage; `stage_id` and `sequence` auto-generated if absent. |
| `update_stage` | `stage_id` (string) | `name`, `sequence`, `purpose`, `outcome`, `sme_notes`, `architect_rationale` | Update an existing Stage. |
| `add_milestone` | `stage_id` (string) | `milestone_id`, `title`, `description`, `completion_criteria`, `evidence_considered` | Create a Milestone under the specified Stage. |
| `update_milestone` | `milestone_id` (string) | `title`, `description`, `completion_criteria`, `evidence_considered` | Update an existing Milestone. |
| `add_evidence` | `stage_id` (string, optional) | `evidence_id`, `evidence_type`, `description`, `demonstrated_proficiency` | Create an Evidence item, optionally attached to a Stage. |
| `add_resource` | `stage_id` (string, optional) | `resource_id`, `title`, `resource_type`, `description`, `reference` | Create a Resource, optionally attached to a Stage. |
| `add_guardrail` | omitted | `guardrail_id`, `category`, `description`, `trigger_conditions`, `escalation_considerations`, `advisor_attention` | Create a Pathway-level Guardrail. |

DELETE operations, arbitrary SQL/database instructions, and automatic Pathway rewrites are explicitly rejected.

## Validation rules

The server validates each proposal at the moment the SME approves it:

1. The `operation` must be in the supported set.
2. Every key in `fields` must be in the allow-list for that operation.
3. Targets must identify entities that exist within the current Pathway.
4. Cross-Pathway and cross-user mutations are rejected by ownership checks.
5. Missing required fields are rejected.
6. Malformed or unexpected response structures are rejected by Pydantic.

## Turn flow

```text
SME sends message
    ↓
Append user message to conversation
    ↓
Build current Pathway context
    ↓
Call AI with system prompt + context + history
    ↓
Parse `ArchitectResponse` using Pydantic/structured output
    ↓
Save the Architect's conversational message
    ↓
Render workspace with the conversational message and the list of proposals
    ↓
SME reviews proposals and decides
    ↓
If SME clicks "Apply Suggestion":
    ↓
    Validate proposal
    ↓
    Begin nested transaction
    ↓
    Apply proposal through model service layer
    ↓
    Commit
    ↓
    Refresh workspace
```

If the AI call or the apply operation fails, the savepoint is rolled back and the existing Pathway state is preserved.

## AI service boundary

- `OPENAI_API_KEY` and `OPENAI_MODEL` are read from the environment.
- The default model is `gpt-4o-mini`.
- The `openai` Python SDK uses `client.beta.chat.completions.parse(..., response_format=ArchitectResponse)`.
- API keys are never logged, exposed in templates, or committed to the repository.

## Testing notes

Unit tests mock `architect.pathway_service.generate_architect_response` to return deterministic `ArchitectResponse` objects. Tests verify that:

- the conversational response is persisted
- the `proposals` list is returned
- the Pathway is not changed without SME approval
- approved, validated proposals are applied and persisted
- rejected proposals leave the Pathway unchanged
- unauthorized or invalid proposals are rejected
