import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import app, db, seed_database
from models import User, InformationDomain, Pathway, Stage


class TestFoundation(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = app.test_client()

        with app.app_context():
            db.create_all()
            seed_database()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_app_initializes(self):
        self.assertIsNotNone(app)
        self.assertIsNotNone(db)

    def test_database_tables_created(self):
        with app.app_context():
            self.assertGreater(User.query.count(), 0)
            self.assertGreater(InformationDomain.query.count(), 0)
            self.assertGreater(Pathway.query.count(), 0)
            self.assertGreater(Stage.query.count(), 0)

    def test_seed_user_can_authenticate(self):
        with app.app_context():
            user = User.query.filter_by(email='sme@example.com').first()
            self.assertIsNotNone(user)
            self.assertTrue(user.check_password('sme123'))
            self.assertTrue(user.is_active())

    def test_protected_routes_require_login(self):
        with app.app_context():
            pathway = Pathway.query.filter_by(name='Loan Readiness').first()

        resp = self.client.get('/')
        self.assertIn(resp.status_code, [302, 401])

        resp = self.client.get(f'/pathway/{pathway.id}/workspace')
        self.assertIn(resp.status_code, [302, 401])

    def test_information_domain_created(self):
        with app.app_context():
            domain = InformationDomain.query.filter_by(name='Small Business Finance').first()
            self.assertIsNotNone(domain)
            self.assertEqual(domain.status, 'active')

    def test_pathway_created(self):
        with app.app_context():
            pathway = Pathway.query.filter_by(name='Loan Readiness').first()
            self.assertIsNotNone(pathway)
            self.assertEqual(pathway.version, '0.1')
            self.assertEqual(pathway.status, 'draft')
            self.assertEqual(pathway.draft_status, 'saved')

    def test_loan_readiness_seed_has_six_stages(self):
        with app.app_context():
            pathway = Pathway.query.filter_by(name='Loan Readiness').first()
            self.assertEqual(len(pathway.stages), 6)

    def test_stages_preserve_sequence(self):
        with app.app_context():
            pathway = Pathway.query.filter_by(name='Loan Readiness').first()
            stages = sorted(pathway.stages, key=lambda s: s.sequence)
            expected = [
                'Define the Financing Need',
                'Understand Business Financials',
                'Assess Owner Financial Preparedness',
                'Evaluate Repayment Capacity',
                'Prepare the Loan Package',
                'Prepare for the Lender Conversation',
            ]
            self.assertEqual([s.name for s in stages], expected)

    def test_workspace_renders_after_login(self):
        with app.app_context():
            pathway = Pathway.query.filter_by(name='Loan Readiness').first()

        self.client.post('/login', data={
            'email': 'sme@example.com',
            'password': 'sme123'
        }, follow_redirects=False)

        resp = self.client.get(f'/pathway/{pathway.id}/workspace')
        self.assertEqual(resp.status_code, 200)

        data = resp.get_data(as_text=True)
        self.assertIn('Loan Readiness', data)
        self.assertIn('Define the Financing Need', data)
        self.assertIn('AI Pathway Architect', data)

    def test_user_cannot_access_another_users_pathway(self):
        with app.app_context():
            pathway = Pathway.query.filter_by(name='Loan Readiness').first()
            pathway_id = pathway.id

            other = User(email='other@example.com', role='SME', active=True)
            other.set_password('other123')
            db.session.add(other)
            db.session.commit()

        # Log in as other user
        self.client.post('/login', data={
            'email': 'other@example.com',
            'password': 'other123'
        }, follow_redirects=False)

        resp = self.client.get(f'/pathway/{pathway_id}/workspace', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)


if __name__ == '__main__':
    unittest.main()
