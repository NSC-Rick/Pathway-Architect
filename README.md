# North Star Pathway Architect

**Phase:** PA-003 — Text Architect Conversation & Structured Pathway Evolution

North Star Pathway Architect is the sister application to North Star Proficiency Builder. Proficiency Builder *runs* Pathways. Pathway Architect *creates* them.

This application is being built as a separate, self-contained Flask project. It does not modify, depend on, or connect to the Proficiency Builder repository or database.

## What is implemented in PA-003

- Text-only conversation with the AI Pathway Architect in the right-hand workspace panel
- Conversation persistence (`ArchitectConversation`, `ArchitectMessage`)
- Deterministic, testable Pathway context serialization for the Architect
- Structured two-part AI response contract (`message` + `proposals`)
- Pydantic response schema validated by `openai` structured-output parsing
- Dedicated `architect/` service package:
  - `prompts.py` — Architect system behavior
  - `context.py` — current Pathway serialization
  - `schemas.py` — structured response and proposal definitions
  - `ai_service.py` — OpenAI API interaction
  - `validation.py` — server-side proposal validation
  - `pathway_service.py` — apply validated operations through the model layer
- Server-side validation of all proposed Pathway mutations
- Constrained mutation vocabulary: `update_pathway`, `add_stage`, `update_stage`, `add_milestone`, `update_milestone`, `add_evidence`, `add_resource`, `add_guardrail`
- Transaction-safe application of related proposals with savepoint rollback on failure
- Workspace that reflects persisted Pathway changes after a successful Architect turn
- Opening discovery question for new and lightly developed Pathways
- Artifact-vs-demonstrated-proficiency reasoning guidance in the Architect prompt
- Ownership and access-control checks preserved from PA-002
- Deterministic unit tests for conversation, validation, persistence, and workspace

## What is NOT implemented in PA-003

- ElevenLabs or any voice/audio integration
- Browser microphone or speech-to-text
- Pathway publishing or Proficiency Builder synchronization
- Pathway Intelligence, analytics, billing, multi-tenancy, or complex versioning
- Real-time streaming UI or frontend frameworks

## Required environment configuration

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Required values:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session and CSRF protection |
| `DATABASE_URL` | Optional PostgreSQL; leave empty for SQLite `data/architect.db` |
| `OPENAI_API_KEY` | Your OpenAI API key (required for live Architect conversation) |
| `OPENAI_MODEL` | OpenAI model to use, e.g. `gpt-4o-mini` |

Do not commit `.env` or any API key. `data/*.db` is already ignored.

## Local setup

1. Create a virtual environment (recommended):

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure `.env` with your `SECRET_KEY` and, for live Architect testing, `OPENAI_API_KEY`.

## Database initialization and seeding

With the virtual environment active, from the project root:

```bash
flask --app app init-db
flask --app app seed-data
```

Seed users:

- SME: `sme@example.com` / `sme123`
- Admin: `admin@example.com` / `admin123`

## Running locally

```bash
flask --app app run
```

Then open http://127.0.0.1:5000 and log in as the SME user.

## Running tests

```bash
python -m unittest discover tests -v
```

AI unit tests mock the `generate_architect_response` boundary so they do not require a live paid API call.

## Live AI verification

With `OPENAI_API_KEY` configured:

1. Log in as the SME user.
2. Open the seeded **Loan Readiness** Pathway.
3. In the Architect panel, type:  
   "When someone comes to us well prepared for a loan, they understand why they need the money, know their numbers, and have thought about how the business will repay it."
4. Continue the conversation.
5. Test the artifact-vs-proficiency distinction:  
   - "They need their financial statements."  
   - "They need to understand them, not just have them."
6. Verify that the left-hand workspace updates with any valid structured proposals.

If `OPENAI_API_KEY` is not configured, the Architect route will show a calm error and the Pathway will not be modified.

## Project structure

```text
Pathway-Architect/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── Procfile
├── init_render.py
├── docs/
│   ├── PA_POC_APPLICATION_SPEC_v0.1.md
│   └── PA_003_ARCHITECT_CONTRACT.md
├── architect/
│   ├── __init__.py
│   ├── prompts.py
│   ├── context.py
│   ├── schemas.py
│   ├── ai_service.py
│   ├── validation.py
│   └── pathway_service.py
├── models/
│   ├── __init__.py
│   └── models.py
├── templates/
├── static/css/
├── data/
└── tests/
    ├── test_foundation.py
    └── test_architect.py
```

## Notes

- This application uses its own SQLite database by default.
- It does not connect to North Star Proficiency Builder's production PostgreSQL database.
- Voice and ElevenLabs are explicitly out of scope for PA-003.
- The live AI conversation quality depends on the configured model and API availability.
