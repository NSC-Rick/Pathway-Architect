# North Star Pathway Architect

**Phase:** PA-002 — Application Foundation & Pathway Workspace

North Star Pathway Architect is the sister application to North Star Proficiency Builder. Proficiency Builder *runs* Pathways. Pathway Architect *creates* them.

This application is being built as a separate, self-contained Flask project. It does not modify, depend on, or connect to the Proficiency Builder repository or database.

## What is implemented in PA-002

- Separate Flask application with its own database
- SQLAlchemy models for User, Information Domain, Pathway, Stage, Milestone, Evidence, Resource, and Guardrail
- Seed data including the Small Business Finance domain and the Loan Readiness reference Pathway
- Simple Flask-Login authentication for SME and Admin roles
- Home dashboard showing Information Domains and Pathways
- Manual Pathway creation
- Pathway Workspace with the seeded Loan Readiness structure
- Manual editing of Pathway details and stage names/outcomes
- North Star visual design language adapted from Proficiency Builder
- Foundation unit tests

## What is NOT implemented in PA-002

- AI Pathway Architect behavior
- OpenAI integration
- Conversation extraction
- ElevenLabs voice integration
- Pathway publishing or Proficiency Builder synchronization
- Pathway Intelligence, analytics, versioning, or multi-tenancy

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

3. Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and set a `SECRET_KEY`. For local development you can leave `DATABASE_URL` empty to use SQLite at `data/architect.db`.

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
python -m unittest tests.test_foundation -v
```

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
│   └── PA_POC_APPLICATION_SPEC_v0.1.md
├── architect/
│   └── __init__.py
├── models/
│   ├── __init__.py
│   └── models.py
├── templates/
├── static/css/
├── data/
└── tests/
    └── test_foundation.py
```

## Notes

- This application uses its own SQLite database by default.
- It does not connect to North Star Proficiency Builder's production PostgreSQL database.
- AI and voice features are planned for PA-003 and PA-004.
