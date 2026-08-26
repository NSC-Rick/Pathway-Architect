from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    pathways = db.relationship('Pathway', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_active(self):
        return self.active


class InformationDomain(db.Model):
    __tablename__ = 'information_domains'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), nullable=False, default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    pathways = db.relationship('Pathway', backref='information_domain', lazy=True)


class Pathway(db.Model):
    __tablename__ = 'pathways'

    id = db.Column(db.Integer, primary_key=True)
    pathway_id = db.Column(db.String(100), unique=True, nullable=False)
    information_domain_id = db.Column(db.Integer, db.ForeignKey('information_domains.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(255), nullable=False)
    version = db.Column(db.String(20), nullable=False, default='0.1')
    status = db.Column(db.String(50), nullable=False, default='draft')
    purpose = db.Column(db.Text)
    intended_audience = db.Column(db.Text)
    desired_proficiency_outcome = db.Column(db.Text)
    sme_notes = db.Column(db.Text)
    architect_rationale = db.Column(db.Text)
    draft_status = db.Column(db.String(50), nullable=False, default='new')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    stages = db.relationship('Stage', backref='pathway', order_by='Stage.sequence', lazy=True, cascade='all, delete-orphan')
    milestones = db.relationship('Milestone', backref='pathway', lazy=True, cascade='all, delete-orphan')
    evidence_items = db.relationship('Evidence', backref='pathway', lazy=True, cascade='all, delete-orphan')
    resources = db.relationship('Resource', backref='pathway', lazy=True, cascade='all, delete-orphan')
    guardrails = db.relationship('Guardrail', backref='pathway', lazy=True, cascade='all, delete-orphan')


class Stage(db.Model):
    __tablename__ = 'stages'

    id = db.Column(db.Integer, primary_key=True)
    pathway_id = db.Column(db.Integer, db.ForeignKey('pathways.id'), nullable=False)
    stage_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    sequence = db.Column(db.Integer, nullable=False, default=0)
    purpose = db.Column(db.Text)
    outcome = db.Column(db.Text)
    sme_notes = db.Column(db.Text)
    architect_rationale = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    milestones = db.relationship('Milestone', backref='stage', lazy=True, cascade='all, delete-orphan')
    evidence_items = db.relationship('Evidence', backref='stage', lazy=True, cascade='all, delete-orphan')
    resources = db.relationship('Resource', backref='stage', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (db.UniqueConstraint('pathway_id', 'stage_id'),)


class Milestone(db.Model):
    __tablename__ = 'milestones'

    id = db.Column(db.Integer, primary_key=True)
    pathway_id = db.Column(db.Integer, db.ForeignKey('pathways.id'), nullable=False)
    stage_id = db.Column(db.Integer, db.ForeignKey('stages.id'), nullable=True)
    milestone_id = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    completion_criteria = db.Column(db.Text)
    evidence_considered = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint('pathway_id', 'milestone_id'),)


class Evidence(db.Model):
    __tablename__ = 'evidence'

    id = db.Column(db.Integer, primary_key=True)
    pathway_id = db.Column(db.Integer, db.ForeignKey('pathways.id'), nullable=False)
    stage_id = db.Column(db.Integer, db.ForeignKey('stages.id'), nullable=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=True)
    evidence_id = db.Column(db.String(50), nullable=False)
    evidence_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    demonstrated_proficiency = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint('pathway_id', 'evidence_id'),)


class Resource(db.Model):
    __tablename__ = 'resources'

    id = db.Column(db.Integer, primary_key=True)
    pathway_id = db.Column(db.Integer, db.ForeignKey('pathways.id'), nullable=False)
    stage_id = db.Column(db.Integer, db.ForeignKey('stages.id'), nullable=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=True)
    resource_id = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    reference = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint('pathway_id', 'resource_id'),)


class Guardrail(db.Model):
    __tablename__ = 'guardrails'

    id = db.Column(db.Integer, primary_key=True)
    pathway_id = db.Column(db.Integer, db.ForeignKey('pathways.id'), nullable=False)
    guardrail_id = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    trigger_conditions = db.Column(db.Text)
    escalation_considerations = db.Column(db.Text)
    advisor_attention = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint('pathway_id', 'guardrail_id'),)


class ArchitectConversation(db.Model):
    __tablename__ = 'architect_conversations'

    id = db.Column(db.Integer, primary_key=True)
    pathway_id = db.Column(db.Integer, db.ForeignKey('pathways.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    messages = db.relationship('ArchitectMessage', backref='conversation', lazy=True, order_by='ArchitectMessage.created_at', cascade='all, delete-orphan')


class ArchitectMessage(db.Model):
    __tablename__ = 'architect_messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('architect_conversations.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
