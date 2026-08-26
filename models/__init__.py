from flask_sqlalchemy import SQLAlchemy

# Single SQLAlchemy instance shared across the application
db = SQLAlchemy()

# Import models so they are registered on the metadata
from .models import (
    User,
    InformationDomain,
    Pathway,
    Stage,
    Milestone,
    Evidence,
    Resource,
    Guardrail,
)
