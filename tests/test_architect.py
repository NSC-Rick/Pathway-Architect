import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import app, db, seed_database
from models import (
    User,
    InformationDomain,
    Pathway,
    Stage,
    Milestone,
    Evidence,
    Resource,
    Guardrail,
    ArchitectConversation,
    ArchitectMessage,
)
from architect.context import build_pathway_context
from architect.prompts import OPENING_MESSAGE
from architect.schemas import ArchitectResponse, Proposal
from architect.pathway_service import process_architect_turn, PathwayServiceError
from architect.validation import validate_proposals, ProposalValidationError
from architect.ai_service import ArchitectAIError


class MockMessage:
    def __init__(self, role, content):
        self.role = role
        self.content = content


def _make_response(message='Understood.', proposals=None):
    return ArchitectResponse(message=message, proposals=proposals or [])


class TestArchitect(unittest.TestCase):

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

    def _pathway(self):
        return Pathway.query.filter_by(name='Loan Readiness').first()

    def _login_as_sme(self):
        self.client.post('/login', data={
            'email': 'sme@example.com',
            'password': 'sme123'
        }, follow_redirects=False)

    # 1. Conversation models/tables initialize.
    def test_conversation_tables_initialize(self):
        with app.app_context():
            self.assertTrue(db.inspect(db.engine).has_table('architect_conversations'))
            self.assertTrue(db.inspect(db.engine).has_table('architect_messages'))

    # 2. Conversation persists across requests.
    @patch('architect.pathway_service.generate_architect_response')
    def test_conversation_persists_across_requests(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()

        mock_ai.return_value = _make_response('Captured that.', [])

        self._login_as_sme()
        self.client.post(f'/pathway/{pathway.id}/architect', data={
            'message': 'They need to understand their numbers.'
        }, follow_redirects=False)

        with app.app_context():
            conversation = ArchitectConversation.query.filter_by(
                pathway_id=pathway.id, user_id=user.id
            ).first()
            self.assertIsNotNone(conversation)
            messages = ArchitectMessage.query.filter_by(
                conversation_id=conversation.id
            ).order_by(ArchitectMessage.created_at).all()
            self.assertGreaterEqual(len(messages), 2)
            self.assertEqual(messages[-2].content, 'They need to understand their numbers.')
            self.assertEqual(messages[-1].content, 'Captured that.')

    # 3. Current Pathway context serializes correctly.
    def test_context_serializes_current_pathway(self):
        with app.app_context():
            pathway = self._pathway()
            context = build_pathway_context(pathway)
            self.assertEqual(context['name'], 'Loan Readiness')
            self.assertEqual(context['information_domain'], 'Small Business Finance')
            self.assertEqual(len(context['stages']), 6)
            self.assertIn('stages', context)
            self.assertIn('milestones', context)
            self.assertIn('evidence_items', context)
            self.assertIn('resources', context)
            self.assertIn('guardrails', context)

    # 4. Architect response schema accepts valid responses.
    def test_schema_accepts_valid_response(self):
        data = {
            'message': 'What does good look like?',
            'proposals': [{
                'operation': 'update_pathway',
                'fields': {'purpose': 'New purpose'},
                'reason': 'Clarified purpose.',
            }]
        }
        response = ArchitectResponse.model_validate(data)
        self.assertEqual(response.message, 'What does good look like?')
        self.assertEqual(len(response.proposals), 1)

    # 5. Architect response schema rejects malformed responses.
    def test_schema_rejects_malformed_response(self):
        with self.assertRaises(Exception):
            ArchitectResponse.model_validate({'proposals': []})
        with self.assertRaises(Exception):
            ArchitectResponse.model_validate({
                'message': 'test',
                'proposals': [],
                'extra_field': 'not allowed',
            })

    # 6. Unknown operations are rejected.
    def test_unknown_operation_rejected(self):
        with app.app_context():
            pathway = self._pathway()
            proposal = Proposal(operation='delete_stage', target='LR-01', fields={})
            with self.assertRaises(ProposalValidationError):
                validate_proposals(pathway, [proposal])

    # 7. Unsupported fields are rejected.
    def test_unsupported_fields_rejected(self):
        with app.app_context():
            pathway = self._pathway()
            proposal = Proposal(
                operation='update_pathway',
                fields={'malicious_sql': 'DROP TABLE users;'},
            )
            with self.assertRaises(ProposalValidationError):
                validate_proposals(pathway, [proposal])

    # 8. Cross-Pathway target mutation is rejected.
    def test_cross_pathway_target_mutation_rejected(self):
        with app.app_context():
            other = Pathway(
                pathway_id='PA-OTHER-001',
                information_domain_id=1,
                user_id=1,
                name='Other Pathway',
                version='0.1',
                status='draft',
            )
            db.session.add(other)
            db.session.flush()
            other_stage = Stage(
                pathway_id=other.id,
                stage_id='OTHER-01',
                name='Other Stage',
                sequence=1,
                outcome='Other outcome.',
            )
            db.session.add(other_stage)
            db.session.commit()

            pathway = self._pathway()
            proposal = Proposal(operation='update_stage', target='OTHER-01', fields={'name': 'Injected'})
            with self.assertRaises(ProposalValidationError):
                validate_proposals(pathway, [proposal])

    # 9. Cross-user mutation is rejected.
    @patch('architect.pathway_service.generate_architect_response')
    def test_cross_user_mutation_rejected(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            other = User(email='other@example.com', role='SME', active=True)
            other.set_password('other123')
            db.session.add(other)
            db.session.commit()

        mock_ai.return_value = _make_response('OK', [])

        with app.app_context():
            with self.assertRaises(PathwayServiceError):
                process_architect_turn(pathway, other, 'I should not be able to do this.')

    # 10. Valid update_pathway operation persists.
    @patch('architect.pathway_service.generate_architect_response')
    def test_valid_update_pathway_persists(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()

        mock_ai.return_value = _make_response('Updated.', [
            Proposal(operation='update_pathway', target=pathway.pathway_id, fields={
                'name': 'Loan Readiness (Refined)',
                'architect_rationale': 'SME clarified the title.',
            })
        ])

        with app.app_context():
            process_architect_turn(pathway, user, 'Call it Loan Readiness (Refined).')

        with app.app_context():
            refreshed = Pathway.query.get(pathway.id)
            self.assertEqual(refreshed.name, 'Loan Readiness (Refined)')

    # 11. Valid update_stage operation persists.
    @patch('architect.pathway_service.generate_architect_response')
    def test_valid_update_stage_persists(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()
            stage = pathway.stages[0]

        mock_ai.return_value = _make_response('Stage updated.', [
            Proposal(operation='update_stage', target=stage.stage_id, fields={
                'name': 'Define the Financing Need (Revised)',
            })
        ])

        with app.app_context():
            process_architect_turn(pathway, user, 'Revise the first stage name.')

        with app.app_context():
            refreshed = Stage.query.get(stage.id)
            self.assertEqual(refreshed.name, 'Define the Financing Need (Revised)')

    # 12. Valid add_milestone operation persists.
    @patch('architect.pathway_service.generate_architect_response')
    def test_valid_add_milestone_persists(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()
            stage = pathway.stages[0]

        mock_ai.return_value = _make_response('Milestone added.', [
            Proposal(operation='add_milestone', target=stage.stage_id, fields={
                'title': 'Confirm loan amount and use',
                'description': 'Owner can state exact amount.',
            })
        ])

        with app.app_context():
            process_architect_turn(pathway, user, 'Add a milestone for confirming the loan amount.')

        with app.app_context():
            refreshed = Pathway.query.get(pathway.id)
            self.assertEqual(len(refreshed.milestones), 1)
            self.assertEqual(refreshed.milestones[0].title, 'Confirm loan amount and use')

    # 13. Valid add_evidence operation persists.
    @patch('architect.pathway_service.generate_architect_response')
    def test_valid_add_evidence_persists(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()
            stage = pathway.stages[1]

        mock_ai.return_value = _make_response('Evidence captured.', [
            Proposal(operation='add_evidence', target=stage.stage_id, fields={
                'evidence_type': 'observation',
                'description': 'Owner describes financial condition.',
                'demonstrated_proficiency': 'Owner can explain the financial condition.',
            })
        ])

        with app.app_context():
            process_architect_turn(pathway, user, 'They must be able to explain the financials.')

        with app.app_context():
            refreshed = Pathway.query.get(pathway.id)
            self.assertEqual(len(refreshed.evidence_items), 1)
            self.assertIn('Owner can explain the financial condition', refreshed.evidence_items[0].demonstrated_proficiency)

    # 14. Valid add_resource operation persists.
    @patch('architect.pathway_service.generate_architect_response')
    def test_valid_add_resource_persists(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()
            stage = pathway.stages[0]

        mock_ai.return_value = _make_response('Resource added.', [
            Proposal(operation='add_resource', target=stage.stage_id, fields={
                'title': 'Loan Need Worksheet',
                'resource_type': 'worksheet',
                'description': 'A worksheet to define the financing need.',
            })
        ])

        with app.app_context():
            process_architect_turn(pathway, user, 'Add a worksheet for the first stage.')

        with app.app_context():
            refreshed = Pathway.query.get(pathway.id)
            self.assertEqual(len(refreshed.resources), 1)
            self.assertEqual(refreshed.resources[0].title, 'Loan Need Worksheet')

    # 15. Valid add_guardrail operation persists.
    @patch('architect.pathway_service.generate_architect_response')
    def test_valid_add_guardrail_persists(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()

        mock_ai.return_value = _make_response('Guardrail added.', [
            Proposal(operation='add_guardrail', fields={
                'category': 'Escalation',
                'description': 'Escalate to lender when owner cannot explain purpose.',
                'advisor_attention': True,
            })
        ])

        with app.app_context():
            process_architect_turn(pathway, user, 'Flag when the owner cannot explain the purpose.')

        with app.app_context():
            refreshed = Pathway.query.get(pathway.id)
            self.assertEqual(len(refreshed.guardrails), 1)
            self.assertTrue(refreshed.guardrails[0].advisor_attention)

    # 16. Failed validation leaves Pathway unchanged.
    @patch('architect.pathway_service.generate_architect_response')
    def test_failed_validation_leaves_pathway_unchanged(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()
            original_name = pathway.name
            original_stage_count = len(pathway.stages)

        mock_ai.return_value = _make_response('Attempting changes.', [
            Proposal(operation='add_stage', fields={'name': 'Good Stage'}),
            Proposal(operation='bad_operation', fields={}),
        ])

        with app.app_context():
            with self.assertRaises(PathwayServiceError):
                process_architect_turn(pathway, user, 'Try to add a stage and an invalid op.')

        with app.app_context():
            refreshed = Pathway.query.get(pathway.id)
            self.assertEqual(refreshed.name, original_name)
            self.assertEqual(len(refreshed.stages), original_stage_count)

    # 17. Multiple related operations are transaction-safe.
    @patch('architect.pathway_service.generate_architect_response')
    def test_multiple_valid_operations_apply_together(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()
            original_stage_count = len(pathway.stages)

        mock_ai.return_value = _make_response('Two valid changes.', [
            Proposal(operation='update_pathway', fields={'purpose': 'Clarified purpose.'}),
            Proposal(operation='add_stage', fields={
                'name': 'Review Commitment',
                'outcome': 'Owner can restate the commitment.',
            }),
        ])

        with app.app_context():
            process_architect_turn(pathway, user, 'Add a review stage and clarify purpose.')

        with app.app_context():
            refreshed = Pathway.query.get(pathway.id)
            self.assertEqual(refreshed.purpose, 'Clarified purpose.')
            self.assertEqual(len(refreshed.stages), original_stage_count + 1)

    # 18. Workspace renders conversation history.
    @patch('architect.pathway_service.generate_architect_response')
    def test_workspace_renders_conversation_history(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()

        mock_ai.return_value = _make_response('I see three dimensions of readiness.')

        self._login_as_sme()
        resp = self.client.get(f'/pathway/{pathway.id}/workspace')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(OPENING_MESSAGE, resp.get_data(as_text=True))

        self.client.post(f'/pathway/{pathway.id}/architect', data={
            'message': 'They understand their numbers.'
        }, follow_redirects=False)

        resp = self.client.get(f'/pathway/{pathway.id}/workspace')
        self.assertIn('They understand their numbers.', resp.get_data(as_text=True))
        self.assertIn('I see three dimensions of readiness.', resp.get_data(as_text=True))

    # 19. Workspace reflects persisted Pathway updates.
    @patch('architect.pathway_service.generate_architect_response')
    def test_workspace_reflects_persisted_pathway_updates(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()

        mock_ai.return_value = _make_response('Name updated.', [
            Proposal(operation='update_pathway', fields={'name': 'Loan Readiness Plus'})
        ])

        self._login_as_sme()
        self.client.post(f'/pathway/{pathway.id}/architect', data={
            'message': 'Rename it Loan Readiness Plus.'
        }, follow_redirects=False)

        resp = self.client.get(f'/pathway/{pathway.id}/workspace')
        self.assertIn('Loan Readiness Plus', resp.get_data(as_text=True))

    # 20. AI/API failure does not corrupt Pathway.
    @patch('architect.pathway_service.generate_architect_response')
    def test_ai_failure_does_not_corrupt_pathway(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()
            original_name = pathway.name

        mock_ai.side_effect = ArchitectAIError('OpenAI API unavailable')

        with app.app_context():
            with self.assertRaises(PathwayServiceError):
                process_architect_turn(pathway, user, 'This should fail safely.')

        with app.app_context():
            refreshed = Pathway.query.get(pathway.id)
            self.assertEqual(refreshed.name, original_name)

    # Extra: add_stage persists.
    @patch('architect.pathway_service.generate_architect_response')
    def test_valid_add_stage_persists(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()
            original_count = len(pathway.stages)

        mock_ai.return_value = _make_response('Stage added.', [
            Proposal(operation='add_stage', fields={
                'name': 'Confirm Follow-Up Plan',
                'outcome': 'Owner knows the next step.',
            })
        ])

        with app.app_context():
            process_architect_turn(pathway, user, 'Add a follow-up stage.')

        with app.app_context():
            refreshed = Pathway.query.get(pathway.id)
            self.assertEqual(len(refreshed.stages), original_count + 1)

    # Extra: update_milestone persists.
    def test_valid_update_milestone_persists(self):
        with app.app_context():
            pathway = self._pathway()
            stage = pathway.stages[0]
            milestone = Milestone(
                pathway_id=pathway.id,
                stage_id=stage.id,
                milestone_id='MIL-01',
                title='Original title',
                description='Original',
            )
            db.session.add(milestone)
            db.session.commit()

            proposal = Proposal(operation='update_milestone', target='MIL-01', fields={
                'title': 'Revised title',
            })
            validate_proposals(pathway, [proposal])
            from architect.pathway_service import _apply_proposals
            _apply_proposals(pathway, [proposal])
            db.session.commit()

            self.assertEqual(milestone.title, 'Revised title')

    # Generalization: artifact-vs-proficiency reasoning is domain-independent.
    def test_artifact_vs_proficiency_reasoning_project_management(self):
        with app.app_context():
            domain = InformationDomain.query.filter_by(name='Small Business Finance').first()
            user = User.query.filter_by(email='sme@example.com').first()
            pathway = Pathway(
                pathway_id='PA-PROJECT-001',
                information_domain_id=domain.id,
                user_id=user.id,
                name='Project Management Basics',
                version='0.1',
                status='draft',
            )
            db.session.add(pathway)
            db.session.commit()

            context = build_pathway_context(pathway)
            self.assertEqual(context['name'], 'Project Management Basics')

            proposal = Proposal(operation='add_stage', fields={
                'name': 'Use the Project Plan',
                'outcome': 'Project manager can explain, maintain, adapt, and use the plan to manage delivery.',
            })
            validate_proposals(pathway, [proposal])
            from architect.pathway_service import _apply_proposals
            _apply_proposals(pathway, [proposal])
            db.session.commit()

            refreshed = Pathway.query.get(pathway.id)
            self.assertEqual(refreshed.stages[0].outcome,
                             'Project manager can explain, maintain, adapt, and use the plan to manage delivery.')


if __name__ == '__main__':
    unittest.main()
