import os
import click
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from models import db, User, InformationDomain, Pathway, Stage, Milestone, Evidence, Resource, Guardrail

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    db_path = os.path.join(app.root_path, 'data', 'architect.db')
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path.replace('\\', '/')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
if not app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def require_role(role):
    def decorator(f):
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role != role:
                flash('Access denied.', 'error')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator


def _user_pathways_query():
    if current_user.role == 'ADMIN':
        return Pathway.query
    return Pathway.query.filter_by(user_id=current_user.id)


def _can_access_pathway(pathway):
    return current_user.role == 'ADMIN' or pathway.user_id == current_user.id


def _generate_pathway_id():
    return f'PA-{datetime.utcnow().strftime("%Y%m%d%H%M%S%f")}'


def seed_database():
    """Seed development data. Safe to call multiple times because it checks for existing records."""
    if User.query.count() > 0:
        return

    sme = User(email='sme@example.com', role='SME', active=True)
    sme.set_password('sme123')
    db.session.add(sme)

    admin = User(email='admin@example.com', role='ADMIN', active=True)
    admin.set_password('admin123')
    db.session.add(admin)

    db.session.flush()

    domain = InformationDomain(
        name='Small Business Finance',
        description='Information, skills, and tools relevant to small-business financing.',
        status='active'
    )
    db.session.add(domain)
    db.session.flush()

    pathway = Pathway(
        pathway_id='PA-LOAN-READINESS',
        information_domain_id=domain.id,
        user_id=sme.id,
        name='Loan Readiness',
        version='0.1',
        status='draft',
        draft_status='saved',
        purpose='Prepare a small-business owner to pursue financing with confidence and understanding.',
        intended_audience='Small-business owners seeking financing',
        desired_proficiency_outcome=(
            'A business completing Loan Readiness should not merely possess a complete loan package. '
            'The owner should be able to have an informed financing conversation with a lender and understand '
            'the financial reasoning behind the request.'
        ),
        sme_notes='Reference/seed content for PA-002. Not a finalized banking methodology.',
        architect_rationale='Seed structure demonstrating the PA-002 Pathway Workspace.'
    )
    db.session.add(pathway)
    db.session.flush()

    seed_stages = [
        {
            'stage_id': 'LR-01',
            'name': 'Define the Financing Need',
            'sequence': 1,
            'outcome': 'Owner can explain how much capital is needed, why, when, and how it will be used.',
        },
        {
            'stage_id': 'LR-02',
            'name': 'Understand Business Financials',
            'sequence': 2,
            'outcome': 'Owner can explain the financial condition and performance of the business.',
        },
        {
            'stage_id': 'LR-03',
            'name': 'Assess Owner Financial Preparedness',
            'sequence': 3,
            'outcome': 'Owner understands relevant personal financial considerations and requirements.',
        },
        {
            'stage_id': 'LR-04',
            'name': 'Evaluate Repayment Capacity',
            'sequence': 4,
            'outcome': 'Owner can explain how the business expects to support the proposed debt.',
        },
        {
            'stage_id': 'LR-05',
            'name': 'Prepare the Loan Package',
            'sequence': 5,
            'outcome': 'Required information is complete, current, and internally consistent.',
        },
        {
            'stage_id': 'LR-06',
            'name': 'Prepare for the Lender Conversation',
            'sequence': 6,
            'outcome': 'Owner can confidently explain the request, assumptions, risks, and repayment strategy.',
        },
    ]

    for s in seed_stages:
        stage = Stage(
            pathway_id=pathway.id,
            stage_id=s['stage_id'],
            name=s['name'],
            sequence=s['sequence'],
            outcome=s['outcome'],
        )
        db.session.add(stage)

    db.session.commit()


@app.cli.command('init-db')
def init_db_command():
    """Create database tables."""
    db.create_all()
    click.echo('Initialized the database.')


@app.cli.command('seed-data')
def seed_data_command():
    """Seed development data."""
    seed_database()
    click.echo('Seeded development data.')


@app.route('/')
@login_required
def home():
    domains = InformationDomain.query.filter_by(status='active').all()
    pathways = _user_pathways_query().order_by(Pathway.created_at.desc()).all()
    return render_template('home.html', domains=domains, pathways=pathways)


@app.route('/domain/<int:domain_id>')
@login_required
def domain_detail(domain_id):
    domain = db.session.get(InformationDomain, domain_id)
    if not domain:
        flash('Domain not found.', 'error')
        return redirect(url_for('home'))
    pathways = _user_pathways_query().filter_by(information_domain_id=domain.id).order_by(Pathway.created_at.desc()).all()
    return render_template('domain_detail.html', domain=domain, pathways=pathways)


@app.route('/pathway/new', methods=['GET', 'POST'])
@login_required
def pathway_create():
    domain_id = request.args.get('domain_id', type=int) or request.form.get('domain_id', type=int)
    domain = db.session.get(InformationDomain, domain_id) if domain_id else None
    active_domains = InformationDomain.query.filter_by(status='active').order_by(InformationDomain.name).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        purpose = request.form.get('purpose', '').strip()
        intended_audience = request.form.get('intended_audience', '').strip()
        desired_proficiency_outcome = request.form.get('desired_proficiency_outcome', '').strip()

        if not domain:
            flash('An Information Domain is required.', 'error')
        elif not name:
            flash('Pathway name is required.', 'error')
        else:
            pathway = Pathway(
                pathway_id=_generate_pathway_id(),
                information_domain_id=domain.id,
                user_id=current_user.id,
                name=name,
                version='0.1',
                status='draft',
                draft_status='new',
                purpose=purpose,
                intended_audience=intended_audience,
                desired_proficiency_outcome=desired_proficiency_outcome,
            )
            db.session.add(pathway)
            db.session.commit()
            flash('Pathway created.', 'success')
            return redirect(url_for('workspace', pathway_id=pathway.id))

    return render_template('pathway_create.html', domain=domain, active_domains=active_domains)


@app.route('/pathway/<int:pathway_id>/workspace', methods=['GET', 'POST'])
@login_required
def workspace(pathway_id):
    pathway = _user_pathways_query().filter_by(id=pathway_id).first()
    if not pathway:
        flash('Pathway not found or access denied.', 'error')
        return redirect(url_for('home'))

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'pathway':
            pathway.name = request.form.get('name', '').strip() or pathway.name
            pathway.purpose = request.form.get('purpose', '').strip()
            pathway.intended_audience = request.form.get('intended_audience', '').strip()
            pathway.desired_proficiency_outcome = request.form.get('desired_proficiency_outcome', '').strip()
            db.session.commit()
            flash('Pathway details updated.', 'success')

        elif form_type == 'stage':
            stage_db_id = request.form.get('stage_id', type=int)
            stage = db.session.get(Stage, stage_db_id)
            if stage and stage.pathway_id == pathway.id:
                stage.name = request.form.get('name', '').strip() or stage.name
                stage.outcome = request.form.get('outcome', '').strip()
                db.session.commit()
                flash('Stage updated.', 'success')
            else:
                flash('Stage not found.', 'error')

        return redirect(url_for('workspace', pathway_id=pathway.id))

    return render_template('workspace.html', pathway=pathway)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password) and user.active:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
