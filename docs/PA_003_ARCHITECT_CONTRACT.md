# PA-003 Architect Response Contract

This document defines the structured two-part response contract used by the AI Pathway Architect in PA-003.

## Response schema

The Architect must return a JSON object matching the `ArchitectResponse` Pydantic model:

```json
{
  "message": "Natural-language response shown to the SME.",
  "proposals": [
    {
      "operation": "update_pathway | add_stage | update_stage | add_milestone | update_milestone | add_evidence | add_resource | add_guardrail",
      "target": "identifier when relevant (e.g., stage_id, milestone_id, or pathway_id)",
      "fields": { "field_name": "value" },
      "reason": "Architect rationale for this change."
    }
  ]
}
```

`proposals` may be an empty list if the Architect is only asking a discovery or clarification question.

## Supported mutation operations

| Operation | Target | Allowed fields | Effect |
|---|---|---|---|
| `update_pathway` | `pathway_id` or omitted | `name`, `purpose`, `intended_audience`, `desired_proficiency_outcome`, `sme_notes`, `architect_rationale`, `draft_status` | Update the top-level Pathway record. |
| `add_stage` | omitted | `stage_id`, `name`, `sequence`, `purpose`, `outcome`, `sme_notes`, `architect_rationale` | Create a new Stage; `stage_id` and `sequence` are auto-generated if not provided. |
| `update_stage` | `stage_id` (string) | `name`, `sequence`, `purpose`, `outcome`, `sme_notes`, `architect_rationale` | Update an existing Stage. |
| `add_milestone` | `stage_id` (string) | `milestone_id`, `title`, `description`, `completion_criteria`, `evidence_considered` | Create a Milestone under the specified Stage. |
| `update_milestone` | `milestone_id` (string) | `title`, `description`, `completion_criteria`, `evidence_considered` | Update an existing Milestone. |
| `add_evidence` | `stage_id` (string, optional) | `evidence_id`, `evidence_type`, `description`, `demonstrated_proficiency` | Create an Evidence item, optionally attached to a Stage. |
| `add_resource` | `stage_id` (string, optional) | `resource_id`, `title`, `resource_type`, `description`, `reference` | Create a Resource, optionally attached to a Stage. |
| `add_guardrail` | omitted | `guardrail_id`, `category`, `description`, `trigger_conditions`, `escalation_considerations`, `advisor_attention` | Create a Pathway-level Guardrail. |

DELETE operations and arbitrary SQL/database instructions are explicitly rejected.

## Validation rules

The server validates each proposal before any model is modified:

1. The `operation` must be in the supported set.
2. Every key in `fields` must be in the allow-list for that operation.
3. For `update_stage`, `add_milestone`, `add_evidence`, `add_resource`, and `update_milestone`, the `target` must identify an entity that exists in the current Pathway.
4. Cross-Pathway and cross-user mutations are rejected by ownership checks.
5. Missing required fields (e.g., `title` for `add_milestone`) are rejected.
6. Malformed or unexpected response structures are rejected by Pydantic.

## Mutation flow

```text
SME message
    ↓
Append user message to conversation
    ↓
Build current Pathway context
    ↓
Call AI with system prompt + context + history
    ↓
Parse `ArchitectResponse` using Pydantic/structured output
    ↓
Validate every proposal
    ↓
Begin nested transaction (savepoint)
    ↓
Apply proposals through model service layer
    ↓
Commit savepoint + commit outer transaction
    ↓
Refresh workspace
```

If any step fails, the savepoint is rolled back and the existing Pathway state is preserved.

## AI service boundary

- `OPENAI_API_KEY` and `OPENAI_MODEL` are read from the environment.
- The default model is `gpt-4o-mini`.
- The `openai` Python SDK uses `client.beta.chat.completions.parse(..., response_format=ArchitectResponse)`.
- API keys are never logged, exposed in templates, or committed to the repository.

## Testing notes

Unit tests mock `architect.pathway_service.generate_architect_response` to return deterministic `ArchitectResponse` objects. This lets validation, persistence, and workspace tests run without live API calls.
