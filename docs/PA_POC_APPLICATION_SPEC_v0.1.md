# North Star Pathway Architect — PoC Application Specification v0.1

**Phase:** PA-001 — Discovery & Application Specification  
**Status:** Draft (documentation and architecture only; no application code)  
**Related Application:** North Star Proficiency Builder (PB) — reference implementation  
**Primary Reference Pathway:** Small Business Loan Readiness  
**Date:** 2026-08-26

---

## 1. Executive Summary

North Star Pathway Architect (PA) is the sister application to North Star Proficiency Builder (PB). Where PB *runs* Pathways, PA *creates* them. The goal of PA-001 is to define the initial proof-of-concept (PoC) application so that a subject-matter expert (SME) can have a natural, AI-guided conversation and emerge with a credible structured first-draft Pathway that they are willing to refine.

The core design principle is:

> **Do not ask the SME to design the Pathway. Ask the SME to teach the Architect what "good" looks like.**

The SME should not need to understand instructional design, PB configuration, Pathway schemas, stage/milestone/evidence architecture, AI prompting, or software configuration. PA is a separate application that will share PB's visual and architectural DNA while serving a different user and a different job.

This document defines the product purpose, the relationship to PB, the primary PoC hypothesis, the target SME persona, the primary user journey, functional and behavioral requirements, the proposed data and application architecture, the voice-interaction model, the Pathway definition model, PB patterns to reuse and to avoid, and the acceptance criteria for the first PoC.

---

## 2. Product Purpose

PA is an AI-assisted environment for translating subject-matter expertise into structured proficiency Pathways.

Conceptually, PA performs the following loop:

```text
LISTEN
  ↓
CLARIFY
  ↓
CHALLENGE
  ↓
IDENTIFY PROFICIENCY
  ↓
STRUCTURE
  ↓
DEFINE EVIDENCE
  ↓
IDENTIFY GAPS / GUARDRAILS / RESOURCES
  ↓
PROPOSE PATHWAY
  ↓
SME REVIEWS
  ↓
REFINE
```

The AI performs the translation from domain expertise into Pathway architecture. The SME's job is to explain their domain, answer discovery questions, and validate what the AI proposes.

PA must be **low-friction** and conversation-first. Voice is expected to be the primary discovery and refinement interface. Text may be available as a secondary interaction method. The workspace must show the Pathway emerging in real time as the SME talks.

---

## 3. PA/PB Relationship

PA and PB are sister applications within a shared North Star platform. They must feel unmistakably related but remain separate.

```text
                    NORTH STAR PLATFORM
                           │
                           │
                Shared Pathway Language
                           │
                ┌──────────┴──────────┐
                │                     │
        PATHWAY ARCHITECT     PROFICIENCY BUILDER
                │                     │
          Design Pathways        Run Pathways
          Define outcomes        Coach users
          Define stages          Track progress
          Define milestones      Capture evidence
          Define evidence        Advisor oversight
          Define guardrails      Coaching record
          Attach resources       Storyboard
          Validate structure     Pathway intelligence
```

PB is the reference implementation. PA should inherit PB's proven patterns where appropriate, adapt them where necessary, and avoid carrying forward patterns that are PB-specific.

### What PA is not

PA is **not** another screen or module inside PB. It is a separate application with its own repository, its own development database, and its own initial deployment.

---

## 4. Primary PoC Hypothesis

The first PA PoC must answer one primary question:

> **Can a knowledgeable subject-matter expert have a natural AI-guided conversation and emerge with a credible structured first-draft Pathway that they would be willing to refine?**

That is the primary proof. The PoC must not expand into a complete enterprise Pathway management system.

---

## 5. Target User / SME Persona

The primary user is a **subject-matter expert** (SME) who is qualified to teach an information domain but is not an instructional designer and does not know PB's internal Pathway schema.

### Persona: Banking SME

- **Role:** Banker, lender, or small-business finance specialist
- **Goal:** Create a Loan Readiness Pathway for small-business owners
- **Knowledge:** Deep understanding of what makes a borrower ready for a financing conversation
- **Constraints:** No time to learn instructional design or schema formats
- **Success:** The SME explains what good looks like; the Architect turns it into a structured Pathway

Other possible SME personas for future domains: project management practitioner, change-management practitioner, AI proficiency specialist.

### Must-not-require list

The SME must not be asked or required to understand:

- Instructional design
- PB configuration
- Pathway schemas
- Stage architecture
- Milestone architecture
- Evidence architecture
- AI prompting
- Software configuration

---

## 6. Primary User Journey

```text
SME logs in to Pathway Architect
        ↓
SME selects / creates an Information Domain
        ↓
SME creates a new Pathway
        ↓
SME begins conversation with the AI Pathway Architect
        ↓
Architect interviews the SME
        ↓
Architect identifies proficiency outcomes
        ↓
Architect proposes structure
        ↓
Pathway structure becomes visible in workspace
        ↓
SME continues the conversation
        ↓
Architect challenges / clarifies / refines
        ↓
Stages, milestones, evidence, resources, and guardrails evolve
        ↓
SME reviews the structured Pathway
        ↓
Draft is saved
```

---

## 7. Functional Requirements

### 7.1 Authentication and user management

- Simple role-based login (SME and Admin for PoC).
- Users can create and update their own Pathway drafts.
- Admins can manage Information Domains and view all drafts.

### 7.2 Information Domain selection/creation

- SMEs can select from a short list of available Information Domains (e.g., Small Business Finance).
- Admins can create new Information Domains.
- The PoC does not require complex domain catalog management.

### 7.3 Pathway creation

- SME creates a new Pathway within an Information Domain.
- The Pathway is created in `draft` status.
- Basic identity fields: name, purpose, intended audience, desired proficiency outcome.

### 7.4 Conversational Pathway design

- The SME can start a conversation with the AI Pathway Architect.
- Voice is the primary channel; text may be available.
- The Architect interviews, challenges, and structures based on the SME's input.

### 7.5 Real-time Pathway workspace

- The workspace displays the current Pathway draft as it evolves.
- Stages, milestones, evidence, resources, and guardrails are shown in a structured view.
- The workspace updates as the conversation produces validated changes.

### 7.6 Manual correction and refinement

- The SME can correct the Architect (e.g., delete or rename a stage, adjust an outcome).
- The SME can continue the conversation to refine the draft.
- The Architect should incorporate corrections and avoid reintroducing the same error.

### 7.7 Save and retrieve drafts

- The draft can be saved at any point.
- The SME can return to a previous draft and continue the conversation.
- The PoC does not require publishing to PB.

### 7.8 Review summary

- A concise architecture summary is visible at the bottom of the workspace.
- It shows the current proficiency outcome, stage sequence, and key evidence types.

---

## 8. Architect Behavioral Requirements

The Architect must behave as a thoughtful Pathway design partner, not a passive summarizer.

### Required behaviors

- Ask open discovery questions.
- Identify desired outcomes.
- Identify what "good" looks like.
- Identify sequencing and dependencies.
- Clarify ambiguous concepts.
- Challenge assumptions.
- Distinguish knowledge from capability.
- Distinguish artifacts from proficiency (see Section 9).
- Identify appropriate evidence.
- Identify missing stages.
- Identify supporting resources and tools.
- Identify guardrails and escalation considerations.
- Propose structures and explain them.
- Ask the SME to validate.
- Revise based on SME feedback.

### Artifact vs. proficiency

PA must actively help SMEs distinguish:

> **Completion** (the artifact exists)  
> from  
> **Demonstrated proficiency** (the person can apply or explain it).

**Weak:** "Borrower uploaded financial statements."  
**Stronger:** "Borrower can explain the financial condition of the business using their financial statements."

The Architect should be capable of asking:

> "You've identified preparing projections as a milestone. What evidence would demonstrate that the owner understands the assumptions rather than simply possessing a spreadsheet?"

### Conversation loop

```text
LISTEN → EXTRACT → CLARIFY → CHALLENGE → STRUCTURE → TEST → REVISE
```

---

## 9. Voice Interaction Model

### Reuse of PB's ElevenLabs pattern

PB's voice integration is the reference implementation. The same pattern should be adapted for PA:

- **Server side:** A `VoiceService` class that calls the ElevenLabs `/convai/conversation/get-signed-url` endpoint and builds a session configuration.
- **Client side:** A bundled JavaScript module that imports the official `@elevenlabs/client` SDK and calls `Conversation.startSession()` with the signed URL and config.
- **Identity round-trip:** Application session ID and user ID are passed to the agent in `custom_llm_extra_body` so the conversation can be associated back to the SME and draft.
- **Completion handling:** When the conversation ends, the client or a webhook sends conversation data to the server, which normalizes it into a standard message format and runs the Pathway-extraction pipeline.

### Differences from PB

- PB's agent is the **AI Recovery Coach**. PA's agent is the **AI Pathway Architect**.
- PB's voice context is the client's coaching state. PA's voice context is the current Pathway draft and the SME's conversation history.
- PB's extraction updates the Coaching Record (commitments, risks, etc.). PA's extraction updates the Pathway draft (stages, milestones, evidence, resources, guardrails, rationale).

### Proposed ElevenLabs architecture for PA

1. **Session initialization**
   - SME clicks **Start Conversation** in the workspace.
   - Server creates a `Conversation` record linked to the current `Pathway` draft.
   - Server calls ElevenLabs to get a signed URL.
   - Server builds a session config with:
     - Agent ID and user ID
     - Pathway name and current draft state
     - SME name
     - Application session and draft IDs
     - A system prompt defining the AI Pathway Architect role

2. **Dynamic context required**
   - Current Pathway draft (stages, outcomes, evidence, resources, guardrails)
   - Current conversation summary
   - Information Domain context
   - Architect's previous insights and open questions

3. **Conversation outputs**
   - The client receives the conversation transcript and posts it to the server.
   - The server normalizes the transcript into a list of `ConversationMessage` records.
   - The server runs an extraction pass to identify proposed Pathway changes.

4. **Structured Pathway updates**
   - The extraction produces a JSON patch or structured update object.
   - The server validates the update against the Pathway schema.
   - Valid updates are persisted to the draft.
   - The workspace re-renders to show the new structure.

5. **Boundaries**
   - The voice conversation is the interface; it does not directly mutate the Pathway.
   - All changes pass through the extraction and validation layer.
   - The server, not the voice agent, owns the authoritative Pathway state.

**Note:** ElevenLabs integration is not implemented in PA-001. This section documents the planned architecture only.

---

## 10. Pathway Definition Model

The PA PoC should support a Pathway definition that can eventually align with the PB Pathway Package v1 and Pathway Runtime Contract concepts.

### Core Pathway fields

- `pathway_id` — stable machine identifier
- `name` — human-readable name
- `status` — `draft`, `poc`, `pilot`, `active`, `inactive`, `retired`
- `version` — version string
- `information_domain_id` — link to Information Domain
- `purpose` — why the Pathway exists
- `intended_audience` — who it is for
- `desired_proficiency_outcome` — what the learner should be able to do
- `sme_notes` — free-form notes from the SME
- `architect_rationale` — design rationale captured by the AI
- `draft_status` — `new`, `interviewing`, `review`, `saved`
- `created_at`, `updated_at`

### Stage fields

- `stage_id` — unique within the Pathway
- `name`
- `purpose` / `outcome`
- `sequence` — ordering
- `sme_notes`
- `architect_rationale`

### Milestone fields

- `milestone_id`
- `stage_id` — parent stage
- `title`
- `description`
- `completion_criteria`
- `evidence_considered`

### Evidence / completion criteria

- `evidence_id`
- `milestone_id` or `stage_id`
- `description` — what observable signal would indicate proficiency
- `evidence_type` — `observation`, `artifact`, `reflection`, `advisor_assessment`
- `demonstrated_proficiency` — the behavior or capability the evidence should show

### Resources / tools

- `resource_id`
- `title`
- `resource_type` — `tool`, `worksheet`, `guide`, `video`, `model`, `reference`
- `description`
- `location` or `reference` (may be null in PoC)
- `related_stage_id` or `related_milestone_id`

### Guardrails

- `guardrail_id`
- `category`
- `description`
- `trigger_conditions`
- `escalation_considerations`
- `advisor_attention` (boolean, for future use)

### SME notes and Architect rationale

- Every major element (Pathway, Stage, Milestone, Evidence, Guardrail) should support both SME notes and Architect rationale.
- SME notes capture the expert's language.
- Architect rationale captures why the AI structured it that way.

### Versioning (future)

- The data model should anticipate Pathway versioning (e.g., `PathwayVersion` table or a `version` field on `Pathway`).
- Versioning is **not** implemented in the PoC.
- A simple `version` string on `Pathway` is sufficient for now.

---

## 11. Proposed Data Model

PA should use SQLAlchemy, like PB, with its own development database (SQLite locally, PostgreSQL on Render). It must not connect to PB's production database.

### Tables

```text
users
  id, email, password_hash, role, active, created_at

information_domains
  id, name, description, status, created_at, updated_at

pathways
  id, pathway_id, name, information_domain_id, version, status,
  purpose, intended_audience, desired_proficiency_outcome,
  sme_notes, architect_rationale, draft_status, created_at, updated_at

stages
  id, pathway_id, stage_id, name, sequence, purpose, outcome,
  sme_notes, architect_rationale, created_at, updated_at

milestones
  id, pathway_id, stage_id, milestone_id, title, description,
  completion_criteria, evidence_considered, created_at, updated_at

evidence
  id, pathway_id, milestone_id (optional), stage_id (optional),
  evidence_id, evidence_type, description, demonstrated_proficiency,
  created_at, updated_at

resources
  id, pathway_id, stage_id (optional), milestone_id (optional),
  resource_id, title, resource_type, description, reference,
  created_at, updated_at

guardrails
  id, pathway_id, guardrail_id, category, description,
  trigger_conditions, escalation_considerations, advisor_attention,
  created_at, updated_at

conversations
  id, pathway_id, user_id, started_at, ended_at, status,
  channel (voice/text), metadata, created_at, updated_at

conversation_messages
  id, conversation_id, role, content, created_at

pathway_draft_snapshots (optional, future)
  id, pathway_id, snapshot, captured_at
```

### Implementation notes

- Use PB's pattern of `db = SQLAlchemy()` in `models/models.py`, initialized in `app.py`.
- Use `db.session.get(Model, id)` for lookups.
- Use `created_at` and `updated_at` timestamps with `onupdate` for updates.
- Keep the PoC schema simple; JSON or text columns may be used for flexible structured data if needed.

---

## 12. Proposed Application Architecture

PA should be a separate Flask application with a structure clearly related to PB.

### Suggested project structure

```text
Pathway-Architect/
│
├── app.py                        # Main Flask application
├── requirements.txt              # Python dependencies (mirror PB stack)
├── .env.example                  # Environment variable template
├── .gitignore
├── Procfile                      # Render start command
├── init_render.py                # Render initialization (optional)
│
├── docs/                         # PA-specific documentation
│   └── PA_POC_APPLICATION_SPEC_v0.1.md
│
├── architect/                    # AI / voice / extraction modules
│   ├── __init__.py
│   ├── ai_service.py             # OpenAI abstraction
│   ├── prompts.py                # System and extraction prompts
│   ├── extraction.py             # Structured update extraction
│   ├── context.py                # Draft context assembly
│   ├── voice_service.py          # ElevenLabs integration
│   └── validation.py             # Extraction validation
│
├── models/
│   ├── __init__.py
│   └── models.py                 # SQLAlchemy models
│
├── templates/
│   ├── base.html                 # Shared base template
│   ├── login.html
│   ├── home.html                 # Domain / Pathway list
│   └── workspace.html            # Split-screen design interface
│
├── static/
│   ├── css/
│   │   └── app.css               # Adapted from PB design system
│   └── js/
│       └── voice-client.js       # ElevenLabs SDK client module
│
├── pathways/                     # Reference / seed Pathways
│   └── (loan_readiness reference content)
│
└── tests/
    └── test_architect.py
```

### Major components

- **Web layer (app.py):** Routes for authentication, domain/pathway management, workspace, and voice session lifecycle.
- **Models layer (models/models.py):** SQLAlchemy models for users, domains, pathways, stages, milestones, evidence, resources, guardrails, and conversations.
- **Architect layer (architect/):**
  - `ai_service.py` — OpenAI API abstraction with environment-driven model selection.
  - `prompts.py` — System prompt for the AI Pathway Architect and extraction prompts.
  - `extraction.py` — Parse conversations into structured Pathway updates.
  - `context.py` — Build a concise context object for the AI from the current draft.
  - `voice_service.py` — ElevenLabs signed URL and session configuration.
  - `validation.py` — Validate proposed updates before persistence.

### Technology stack

Mirror PB's proven stack:

- Python 3 / Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- Flask-Login 0.6.3
- Werkzeug 3.0.1
- python-dotenv 1.0.0
- openai Python SDK
- requests
- gunicorn (production)
- SQLite (local) / PostgreSQL via `psycopg[binary]` (Render)

### Configuration

- `SECRET_KEY` for Flask sessions.
- `DATABASE_URL` for PostgreSQL; fallback to SQLite `data/architect.db` if not set.
- `OPENAI_API_KEY` and `OPENAI_MODEL`.
- `ELEVENLABS_API_KEY`, `ELEVENLABS_AGENT_ID` for the AI Pathway Architect agent.
- Environment variables loaded with `python-dotenv`.

---

## 13. UX / Screen Architecture

PA should share PB's visual DNA while being optimized for Pathway creation.

### Design language to inherit from PB

- CSS custom properties for color and spacing (`--primary-color`, `--bg-color`, etc.).
- System-font stack (`-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, etc.).
- Card-based layout (`card` class with shadow and rounded corners).
- Button hierarchy (`btn btn-primary`, `btn btn-secondary`, `btn btn-large`).
- Alert and badge patterns (`alert-success`, `alert-error`, `badge` status classes).
- Form group patterns.
- Responsive, mobile-first behavior with breakpoints at 768px and 480px.
- Base template with navbar, flashed-message handling, and footer.

### Conceptual desktop workspace

```text
-------------------------------------------------------------
| NORTH STAR PATHWAY ARCHITECT                             |
-------------------------------------------------------------
|                              |                            |
| PATHWAY WORKSPACE            | AI PATHWAY ARCHITECT       |
|                              |                            |
| Loan Readiness               | Voice conversation         |
| Small Business Finance       |                            |
| Draft                        | Architect prompts          |
|                              |                            |
| Stage 1                      | SME conversation           |
| Stage 2                      |                            |
| Stage 3                      | Architect insights         |
| Stage 4                      |                            |
| ...                          | Start / End Conversation   |
|                              |                            |
-------------------------------------------------------------
| Architecture summary                                      |
-------------------------------------------------------------
```

### Core UX concept

> **The SME talks on one side while watching the Pathway emerge on the other.**

### Requirements

- Avoid a configuration-heavy interface.
- Do not make SMEs populate large forms to design Pathways.
- The conversation panel should be the primary interaction surface.
- The workspace should update without full page reloads (use fetch + DOM updates or a lightweight JS layer).
- The workspace should be responsive; on mobile, stack the conversation and the draft vertically.
- Provide a visible **Start / End Conversation** control.
- Provide a simple mechanism for the SME to correct the Architect (e.g., inline edit or a "That isn't right" action).

---

## 14. PB Design Patterns to Reuse

PB is the reference implementation. The following patterns are recommended for PA.

| Pattern | Where in PB | Recommendation for PA |
|---------|-------------|-----------------------|
| Flask application structure | `app.py` at project root, `models/`, `coaching/`, `templates/`, `static/` | Mirror the structure in a separate application. |
| SQLAlchemy setup | `models/models.py` `db = SQLAlchemy()`, `db.init_app(app)` in `app.py` | Reuse the same pattern. |
| Model conventions | Timestamps, `db.session.get`, backrefs, `cascade='all, delete-orphan'` | Apply to PA models. |
| Authentication | `User` + `UserMixin`, `set_password` / `check_password`, `LoginManager`, `require_role` | Reuse; define `SME` and `ADMIN` roles. |
| Configuration | `.env.example`, `python-dotenv`, `DATABASE_URL` normalization for `postgresql+psycopg` | Reuse. |
| Service-layer modules | `coaching/ai_service.py`, `coaching/voice_service.py`, `coaching/prompts.py`, `coaching/validator.py`, `coaching/persistence.py` | Create an `architect/` package with analogous modules. |
| Template organization | `templates/base.html` with blocks, flash messages, navbar, footer | Reuse and adapt for PA branding. |
| Base template and navigation | `templates/base.html` | Adapt the nav brand to "North Star Pathway Architect." |
| CSS design system | `static/css/app.css` with variables, `card`, `btn`, `badge`, `alert`, responsive breakpoints | Fork and extend for the split workspace. |
| Typography | System font stack, heading hierarchy | Reuse. |
| Cards, buttons, badges | `static/css/app.css` | Reuse. |
| Forms and spacing | `.form-group`, `.container`, `.main-content` | Reuse. |
| Responsive/mobile behavior | Media queries at 768px and 480px | Reuse and add split-pane collapse. |
| ElevenLabs voice integration | `coaching/voice_service.py`, `frontend/voice-client.js` | Reuse the signed-URL + SDK pattern for the Architect agent. |
| AI/API integration | `coaching/ai_service.py` OpenAI wrapper | Reuse as the LLM backend. |
| Logging | `logging.basicConfig(level=logging.INFO)` and request-aware logging | Reuse but avoid logging secrets. |
| Testing conventions | `tests/test_foundation.py` uses `unittest`, in-memory SQLite, `app.test_client`, setUp/tearDown | Reuse. |
| Render deployment | `Procfile`, `init_render.py`, `DEPLOYMENT.md` | Reuse the build/init pattern for PA. |

---

## 15. PB Patterns NOT to Reuse

PB is a *reference*, not a template. The following patterns are PB-specific and should not carry into PA.

| Pattern | Why it should not be reused |
|---------|------------------------------|
| Client/Advisor/Business models | PA serves SMEs, not coaching clients and advisors. |
| Engagement model | PA has no client engagement or coaching record. |
| PathwayState with `current_day` | PA does not track a learner's day-by-day progress. |
| Commitment, Risk, SignificantEvent, LearningRecord, CoachingObservation | These are Coaching Record constructs; PA has no Coaching Record. |
| Build 002 extraction schema (commitments, risks, etc.) | PA extracts Pathway structure, not client progress. |
| Recovery-specific prompt language | PA's agent is the Pathway Architect, not the Recovery Coach. |
| `PATHWAY_MAP` hard-coded dictionary | PA should not rely on a fixed map; it should create Pathways dynamically. |
| Day-based stage assumptions | PA stages are developmental, not necessarily calendar-based. |
| PB's existing ElevenLabs agent | PA needs a distinct agent with a distinct prompt and configuration. |
| Direct connection to PB's production PostgreSQL database | PA must have its own database in the PoC. |
| PB's admin screens for user/advisor/assignment management | PA can be simpler; no client-advisor assignment. |

---

## 16. Information Domain Approach

PA should anticipate Information Domains without overbuilding domain management.

```text
North Star Platform
    ↓
Information Domain
    ↓
Pathway
    ↓
Pathway Version
    ↓
Stage
    ↓
Milestone
    ↓
Evidence / Resources / Guardrails
```

### PoC scope

- The PoC supports a small, administratively managed list of Information Domains.
- Example domains: Small Business Finance, Small Business, AI Proficiency, Change Management, Project Management.
- For the first PoC, the focus is **Small Business Finance** with the **Loan Readiness** reference Pathway.
- User access to specific domains can be granted by linking a user to an `information_domain_id` or by checking roles in the future. The PoC does not need fine-grained domain permissions.

---

## 17. Draft / Future Versioning Considerations

### PoC

- A `version` string on `Pathway` is sufficient.
- `draft_status` tracks `new`, `interviewing`, `review`, `saved`.
- No formal publishing workflow.

### Future

- Introduce a `PathwayVersion` table or versioned snapshots.
- Track which version was published to PB.
- Support draft → review → active lifecycle.
- Preserve historical drafts for audit and learning.

The data model should not prevent these additions, but they are not implemented in PA-001.

---

## 18. Security / Permission Considerations

- **Authentication:** Passwords hashed with Werkzeug's `generate_password_hash`.
- **Authorization:** Role-based access (`SME`, `ADMIN`).
- **Draft ownership:** SMEs can only access their own Pathway drafts unless explicitly granted broader access.
- **Domain scoping:** SMEs are associated with one or more Information Domains. Admins can manage all domains.
- **API keys and secrets:** Stored in environment variables, not in source control.
- **Voice session security:** Use signed URLs and `custom_llm_extra_body` for identity round-trip, as PB does.
- **Input validation:** Validate all form and JSON inputs server-side.
- **No cross-application database access:** PA must not read or write PB's production database in the PoC.

---

## 19. Loan Readiness Reference Pathway

### Information Domain

Small Business Finance

### Pathway

Loan Readiness

### Overall proficiency outcome

A business completing Loan Readiness should not merely possess a complete loan package. The owner should be able to have an informed financing conversation with a lender and understand the financial reasoning behind the request.

### Stages

**Stage 1 — Define the Financing Need**  
Outcome: Owner can explain how much capital is needed, why, when, and how it will be used.

**Stage 2 — Understand Business Financials**  
Outcome: Owner can explain the financial condition and performance of the business.  
Supporting tool (optional): North Star Finance Modeler

**Stage 3 — Assess Owner Financial Preparedness**  
Outcome: Owner understands relevant personal financial considerations and requirements.

**Stage 4 — Evaluate Repayment Capacity**  
Outcome: Owner can explain how the business expects to support the proposed debt.

**Stage 5 — Prepare the Loan Package**  
Outcome: Required information is complete, current, and internally consistent.

**Stage 6 — Prepare for the Lender Conversation**  
Outcome: Owner can confidently explain the request, assumptions, risks, and repayment strategy.

### Note

This is **reference content**, not a finalized Loan Readiness methodology. The PoC will use it to validate the Architect's behavior and the workspace UI.

---

## 20. Reference Architect Interaction

The following interaction pattern is the behavioral reference for the AI Pathway Architect.

**Architect:**
> "When a small-business owner comes to you really well prepared for a financing conversation, what is different about that person?"

**SME describes:**
- Knowing what they are asking for
- Understanding why financing is needed
- Understanding financials
- Considering repayment
- Having documentation prepared

**Architect extracts candidate dimensions.**

**Architect challenges:**
> "Is having financial statements evidence of financial readiness, or should the owner be able to explain what those statements are telling them about the business?"

**SME clarifies** that understanding matters.

**Architect converts that into demonstrated proficiency.**

Later, the Architect discovers that owner personal financial preparedness is missing and proposes adding another stage.

This illustrates the expected loop:

```text
LISTEN → EXTRACT → CLARIFY → CHALLENGE → STRUCTURE → TEST → REVISE
```

---

## 21. Testing Strategy

### Unit tests

- **Model tests:** Validate Pathway, Stage, Milestone, Evidence, Resource, and Guardrail creation and relationships.
- **Extraction tests:** Provide sample SME/Architect transcripts and verify the extracted Pathway updates.
- **Validation tests:** Verify that invalid updates (missing stage ID, duplicate IDs) are rejected.
- **Voice service tests:** Verify signed URL and session config construction (mocking the ElevenLabs API).

### Integration tests

- **End-to-end conversation flow:** SME creates a Pathway, starts a conversation, and the workspace updates with a new stage.
- **Client isolation:** One SME cannot view another SME's draft.
- **Voice completion flow:** Simulate a completed voice conversation and verify draft persistence.

### Manual tests

- **SME walkthrough:** A knowledgeable SME uses the PoC to create a Loan Readiness draft.
- **Voice quality check:** Verify the Architect agent sounds natural and does not sound like a questionnaire.

### Testing conventions

- Use `unittest` with `app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'`.
- Use `setUp` and `tearDown` to create and drop the in-memory database.
- Use `app.test_client()` for route tests.

---

## 22. PoC Acceptance Criteria

A knowledgeable SME who has never used Pathway Architect can:

1. Create or select a domain.
2. Start a Pathway.
3. Have a natural conversation with the Architect.
4. Explain what proficiency looks like in their field.
5. Be challenged intelligently by the Architect.
6. Watch a structured Pathway emerge.
7. Review stages, outcomes, and evidence.
8. Correct the Architect.
9. Continue refining the Pathway.
10. Save a credible first draft.

The SME should not need to understand PB's internal Pathway schema.

---

## 23. Explicit Out-of-Scope Items

The first PoC does **not** include:

- Enterprise multi-tenancy
- Complex partner administration
- Billing or licensing
- Analytics dashboards
- Production Pathway Intelligence
- Automated PB synchronization
- Sophisticated publishing workflows
- Complex version migration
- Marketplace functionality
- Extensive role management
- Production-scale APIs
- Background workflow infrastructure unless technically required
- Broad domain catalog management
- Direct connection to PB's database
- Voice beyond the signed-URL / completion pattern (no scheduled calls, no transcription storage)
- Mobile native application

---

## 24. Recommended Implementation Phases

| Phase | Focus | Deliverable |
|-------|-------|-------------|
| PA-001 | Discovery & Application Specification | This document |
| PA-002 | Scaffold, database, and basic workspace | Running Flask app with login, domain, and Pathway creation |
| PA-003 | Text-based AI Pathway Architect | SME can chat with the Architect and see the draft update |
| PA-004 | Voice integration | ElevenLabs voice session with the Architect agent |
| PA-005 | Refinement and validation | SME correction, review, save, and PoC acceptance testing |

---

## 25. Risks / Open Questions

### Risks

1. **Prompt size and voice limits:** The Architect prompt may grow as the Pathway becomes complex. Voice prompts must remain concise.
2. **Extraction reliability:** Translating a free-form conversation into a structured Pathway update is non-trivial and may require iteration.
3. **Over-structuring:** The Architect may produce a Pathway that feels too rigid or too generic for the SME's domain.
4. **SME trust:** The SME may not believe the AI understands their domain well enough to design the Pathway.
5. **Separation from PB:** Maintaining a shared Pathway language while keeping PA independent may require future integration work.

### Open questions

1. Should PA use a structured JSON/YAML Pathway package format internally, or should it use a purely database-driven model in the PoC?
2. How frequently should the Architect update the draft — after every turn, after each session, or on explicit save?
3. Should the SME be able to edit the draft directly, or only through conversation?
4. What is the minimum viable voice-agent prompt for the Architect?
5. How should the PoC handle ambiguous or contradictory SME input?
6. What is the right balance between reusing PB's CSS and creating a distinct PA identity?

---

## Appendix A — PB Reference Files Inspected

The following PB files and components were inspected to inform this specification:

- `app.py` — Flask routes, authentication, voice session lifecycle, admin pathways
- `models/models.py` — SQLAlchemy models and conventions
- `coaching/ai_service.py` — OpenAI service abstraction
- `coaching/voice_service.py` — ElevenLabs signed URL and session config
- `templates/base.html` — base template, navigation, and flash messages
- `static/css/app.css` — design system, cards, buttons, badges, responsive layout
- `frontend/voice-client.js` — client-side ElevenLabs SDK integration
- `requirements.txt` — dependency stack
- `.env.example` — environment variable conventions
- `Procfile` and `init_render.py` — Render deployment pattern
- `DEPLOYMENT.md` — deployment guide
- `README.md` — project overview
- `docs/02_ARCHITECTURE.md` — platform architecture
- `docs/04_PATHWAY_SPECIFICATION.md` — Pathway structure
- `docs/PATHWAY_PACKAGE_SPEC_V1.md` — package format
- `docs/PATHWAY_RUNTIME_CONTRACT_V1.md` — runtime contract and adapter concept
- `ELEVENLABS_SETUP.md` — agent configuration guidance
- `tests/test_foundation.py` — testing conventions

---

*End of North Star Pathway Architect — PoC Application Specification v0.1*
