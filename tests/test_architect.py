import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

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
from architect.pathway_service import (
    process_architect_turn,
    apply_architect_proposal,
    PathwayServiceError,
)
from architect.ai_service import ArchitectAIError


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

    def _login_as_other(self):
        other = User(email='other@example.com', role='SME', active=True)
        other.set_password('other123')
        with app.app_context():
            db.session.add(other)
            db.session.commit()
        self.client.post('/login', data={
            'email': 'other@example.com',
            'password': 'other123'
        }, follow_redirects=False)

    # 1. Architect route requires authentication.
    def test_architect_route_requires_authentication(self):
        with app.app_context():
            pathway = self._pathway()

        resp = self.client.post(f'/pathway/{pathway.id}/architect', data={'message': 'test'})
        self.assertEqual(resp.status_code, 302)

        resp = self.client.post(f'/pathway/{pathway.id}/apply', data={'proposal': '{}'})
        self.assertEqual(resp.status_code, 302)

    # 2. User cannot access another user's Pathway conversation.
    def test_user_cannot_access_another_users_pathway_conversation(self):
        with app.app_context():
            pathway = self._pathway()

        self._login_as_other()

        resp = self.client.get(f'/pathway/{pathway.id}/workspace')
        self.assertEqual(resp.status_code, 302)

        resp = self.client.post(f'/pathway/{pathway.id}/architect', data={
            'message': 'I should not be able to do this.'
        })
        self.assertEqual(resp.status_code, 302)

    # 3. Conversation is associated with the correct Pathway.
    @patch('architect.pathway_service.generate_architect_response')
    def test_conversation_associated_with_correct_pathway(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()

        mock_ai.return_value = _make_response('Acknowledged.', [])

        with app.app_context():
            process_architect_turn(pathway, user, 'Describe the loan-ready owner.')

        with app.app_context():
            conversation = ArchitectConversation.query.first()
            self.assertIsNotNone(conversation)
            self.assertEqual(conversation.pathway_id, pathway.id)
            self.assertEqual(conversation.user_id, user.id)

    # 4. SME message persists.
    @patch('architect.pathway_service.generate_architect_response')
    def test_sme_message_persists(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()

        mock_ai.return_value = _make_response('Got it.', [])
        user_content = 'They need to understand their numbers.'

        with app.app_context():
            process_architect_turn(pathway, user, user_content)

        with app.app_context():
            user_msg = ArchitectMessage.query.filter_by(role='user').first()
            self.assertIsNotNone(user_msg)
            self.assertEqual(user_msg.content, user_content)

    # 5. Architect message persists.
    @patch('architect.pathway_service.generate_architect_response')
    def test_architect_message_persists(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()

        mock_ai.return_value = _make_response('I hear four capabilities.', [])

        with app.app_context():
            process_architect_turn(pathway, user, 'They need to know their numbers.')

        with app.app_context():
            architect_msg = ArchitectMessage.query.filter_by(role='architect').order_by(
                ArchitectMessage.created_at.desc()
            ).first()
            self.assertIsNotNone(architect_msg)

    # 6. Conversation history reloads.
    @patch('architect.pathway_service.generate_architect_response')
    def test_conversation_history_reloads(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()

        mock_ai.return_value = _make_response('I see those dimensions.')

        self._login_as_sme()
        self.client.post(f'/pathway/{pathway.id}/architect', data={
            'message': 'They need to know their numbers.'
        })

        resp = self.client.get(f'/pathway/{pathway.id}/workspace')
        data = resp.get_data(as_text=True)
        self.assertIn(OPENING_MESSAGE, data)
        self.assertIn('They need to know their numbers.', data)

    # 7. Architect context includes current Pathway information.
    def test_context_includes_current_pathway_information(self):
        with app.app_context():
            pathway = self._pathway()
            context = build_pathway_context(pathway)

        self.assertEqual(context['name'], 'Loan Readiness')
        self.assertEqual(context['pathway_id'], pathway.pathway_id)
        self.assertIsNotNone(context['purpose'])
        self.assertIsNotNone(context['desired_proficiency_outcome'])
        self.assertEqual(len(context['stages']), 6)

    # 8. Architect context includes Information Domain.
    def test_context_includes_information_domain(self):
        with app.app_context():
            pathway = self._pathway()
            context = build_pathway_context(pathway)

        self.assertEqual(context['information_domain'], 'Small Business Finance')
        self.assertIn('domain_description', context)
        self.assertIsNotNone(context['domain_description'])

    # 9. Structured proposal can be represented separately from conversational response.
    @patch('architect.pathway_service.generate_architect_response')
    def test_structured_proposal_separate_from_conversational_response(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()

        proposals = [
            Proposal(operation='update_pathway', fields={
                'desired_proficiency_outcome': 'Owner can engage credibly with a lender.'
            }, reason='SME emphasized demonstrated capability.')
        ]
        mock_ai.return_value = _make_response('I can refine the outcome.', proposals)

        with app.app_context():
            ai_response = process_architect_turn(pathway, user, 'They must engage with lenders.')

        self.assertEqual(ai_response.message, 'I can refine the outcome.')
        self.assertEqual(len(ai_response.proposals), 1)
        self.assertEqual(ai_response.proposals[0].operation, 'update_pathway')
        self.assertNotEqual(pathway.desired_proficiency_outcome, 'Owner can engage credibly with a lender.')

    # 10. Unauthorized Pathway mutation is prevented.
    def test_unauthorized_pathway_mutation_prevented(self):
        with app.app_context():
            pathway = self._pathway()
            other = User(email='other2@example.com', role='SME', active=True)
            other.set_password('other123')
            db.session.add(other)
            db.session.commit()

            proposal = Proposal(operation='update_pathway', fields={
                'name': 'Loan Readiness Hacked'
            })

            with self.assertRaises(PathwayServiceError):
                apply_architect_proposal(pathway, other, proposal)

            self.assertNotEqual(pathway.name, 'Loan Readiness Hacked')

    # 11. Approved supported proposal updates the correct Pathway field.
    @patch('architect.pathway_service.generate_architect_response')
    def test_approved_proposal_updates_correct_pathway_field(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()

        proposals = [
            Proposal(operation='update_pathway', fields={
                'purpose': 'Prepare a small-business owner for a credible financing conversation.',
                'desired_proficiency_outcome': 'Owner can define the need, understand the financials, and discuss repayment.'
            }, reason='SME clarified the purpose and outcome.')
        ]
        mock_ai.return_value = _make_response('I suggest this refinement.', proposals)

        with app.app_context():
            process_architect_turn(pathway, user, 'They must define the need and understand the numbers.')
            apply_architect_proposal(pathway, user, proposals[0])

        with app.app_context():
            refreshed = Pathway.query.get(pathway.id)
            self.assertEqual(refreshed.purpose, 'Prepare a small-business owner for a credible financing conversation.')
            self.assertEqual(refreshed.desired_proficiency_outcome, 'Owner can define the need, understand the financials, and discuss repayment.')

    # 12. Rejected proposal does not alter the Pathway.
    @patch('architect.pathway_service.generate_architect_response')
    def test_rejected_proposal_does_not_alter_pathway(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()
            original_purpose = pathway.purpose

        proposals = [
            Proposal(operation='update_pathway', fields={
                'purpose': 'A very different purpose.'
            }, reason='Test.')
        ]
        mock_ai.return_value = _make_response('What about this?', proposals)

        with app.app_context():
            process_architect_turn(pathway, user, 'Maybe.')
            # SME does NOT call apply_architect_proposal.

        with app.app_context():
            refreshed = Pathway.query.get(pathway.id)
            self.assertEqual(refreshed.purpose, original_purpose)

    # 13. AI/API failure does not corrupt Pathway state.
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
            # Only the conversation opening message should exist; the failed AI
            # turn should not have added an Architect response.
            self.assertEqual(ArchitectMessage.query.filter_by(role='architect').count(), 1)

    # 14. Apply route updates the workspace.
    @patch('architect.pathway_service.generate_architect_response')
    def test_apply_route_updates_workspace(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()

        proposals = [
            Proposal(operation='update_pathway', fields={
                'purpose': 'A clearer purpose.'
            }, reason='Refined purpose.')
        ]
        mock_ai.return_value = _make_response('I propose this.', proposals)

        self._login_as_sme()
        self.client.post(f'/pathway/{pathway.id}/architect', data={
            'message': 'They must know the purpose.'
        })

        proposal_json = proposals[0].model_dump_json()
        resp = self.client.post(f'/pathway/{pathway.id}/apply', data={
            'proposal': proposal_json
        }, follow_redirects=False)

        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(f'/pathway/{pathway.id}/workspace')
        self.assertIn('A clearer purpose.', resp.get_data(as_text=True))

    # 15. Invalid proposals are rejected by the apply route.
    def test_apply_route_rejects_invalid_proposals(self):
        with app.app_context():
            pathway = self._pathway()

        self._login_as_sme()
        resp = self.client.post(f'/pathway/{pathway.id}/apply', data={
            'proposal': json.dumps({'operation': 'delete_everything', 'fields': {}})
        }, follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        data = resp.get_data(as_text=True)
        self.assertIn('Loan Readiness', data)

    # 16. Existing add/update operations still work when approved.
    @patch('architect.pathway_service.generate_architect_response')
    def test_stage_update_works_when_approved(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()
            stage = pathway.stages[0]

        proposals = [
            Proposal(operation='update_stage', target=stage.stage_id, fields={
                'name': 'Define the Financing Need (Refined)',
            })
        ]
        mock_ai.return_value = _make_response('What about this stage name?', proposals)

        with app.app_context():
            process_architect_turn(pathway, user, 'Refine the first stage.')
            apply_architect_proposal(pathway, user, proposals[0])

        with app.app_context():
            refreshed = Stage.query.get(stage.id)
            self.assertEqual(refreshed.name, 'Define the Financing Need (Refined)')

    # --- PA-003.1 role mapping and error UX tests ---

    @patch('architect.ai_service.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_architect_role_maps_to_openai_assistant(self, mock_openai):
        with app.app_context():
            pathway = self._pathway()
            conversation = ArchitectConversation(pathway_id=pathway.id, user_id=1, status='active')
            db.session.add(conversation)
            db.session.commit()

            user_msg = ArchitectMessage(conversation_id=conversation.id, role='user', content='User says.')
            architect_msg = ArchitectMessage(conversation_id=conversation.id, role='architect', content='Architect says.')
            db.session.add_all([user_msg, architect_msg])
            db.session.commit()

            mock_client = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.parsed = _make_response('Response.', [])
            mock_client.beta.chat.completions.parse.return_value.choices = [mock_choice]
            mock_openai.return_value = mock_client

            from architect.ai_service import generate_architect_response
            generate_architect_response(pathway, [user_msg, architect_msg], 'New message.')

            call = mock_client.beta.chat.completions.parse.call_args
            sent_messages = call.kwargs['messages']
            self.assertEqual(sent_messages[0]['role'], 'system')
            self.assertEqual(sent_messages[1]['role'], 'user')
            self.assertEqual(sent_messages[2]['role'], 'assistant')
            self.assertEqual(sent_messages[3]['role'], 'user')
            self.assertEqual(sent_messages[2]['content'], 'Architect says.')

    @patch('architect.ai_service.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_unknown_persisted_role_defaults_to_user(self, mock_openai):
        with app.app_context():
            pathway = self._pathway()
            conversation = ArchitectConversation(pathway_id=pathway.id, user_id=1, status='active')
            db.session.add(conversation)
            db.session.commit()

            odd_msg = ArchitectMessage(conversation_id=conversation.id, role='narrator', content='Narration.')
            db.session.add(odd_msg)
            db.session.commit()

            mock_client = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.parsed = _make_response('Response.', [])
            mock_client.beta.chat.completions.parse.return_value.choices = [mock_choice]
            mock_openai.return_value = mock_client

            from architect.ai_service import generate_architect_response
            generate_architect_response(pathway, [odd_msg], 'New message.')

            call = mock_client.beta.chat.completions.parse.call_args
            sent_messages = call.kwargs['messages']
            # Unknown role should be mapped to 'user' to avoid an OpenAI 400.
            self.assertEqual(sent_messages[1]['role'], 'user')
            self.assertEqual(sent_messages[1]['content'], 'Narration.')

    @patch('architect.ai_service.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_openai_request_does_not_send_temperature(self, mock_openai):
        with app.app_context():
            pathway = self._pathway()
            conversation = ArchitectConversation(pathway_id=pathway.id, user_id=1, status='active')
            db.session.add(conversation)
            db.session.commit()

            user_msg = ArchitectMessage(conversation_id=conversation.id, role='user', content='User says.')
            db.session.add(user_msg)
            db.session.commit()

            mock_client = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.parsed = _make_response('Response.', [])
            mock_client.beta.chat.completions.parse.return_value.choices = [mock_choice]
            mock_openai.return_value = mock_client

            from architect.ai_service import generate_architect_response
            generate_architect_response(pathway, [user_msg], 'New message.')

            call = mock_client.beta.chat.completions.parse.call_args
            self.assertNotIn('temperature', call.kwargs)

    @patch('architect.pathway_service.generate_architect_response')
    def test_ai_failure_persists_user_message_but_not_architect_message(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()

        mock_ai.side_effect = ArchitectAIError('OpenAI API request failed: 400')

        with app.app_context():
            with self.assertRaises(PathwayServiceError):
                process_architect_turn(pathway, user, 'Persist me on failure.')

        with app.app_context():
            # SME message is saved even though the AI failed.
            self.assertEqual(ArchitectMessage.query.filter_by(role='user', content='Persist me on failure.').count(), 1)
            # No new Architect response is saved beyond the conversation opening message.
            self.assertEqual(ArchitectMessage.query.filter_by(role='architect').count(), 1)

    @patch('architect.pathway_service.generate_architect_response')
    def test_user_facing_error_does_not_expose_provider_details(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()

        mock_ai.side_effect = ArchitectAIError('OpenAI API request failed: 400 - Invalid value: architect')

        self._login_as_sme()
        resp = self.client.post(f'/pathway/{pathway.id}/architect', data={
            'message': 'This should fail gracefully.'
        }, follow_redirects=True)

        data = resp.get_data(as_text=True)
        # Jinja HTML-escapes the apostrophe; match the rendered attribute form.
        self.assertIn('The Architect couldn&#39;t complete that response', data)
        self.assertIn('Your message has been saved', data)
        # Provider-specific details should not appear in the rendered HTML.
        self.assertNotIn('AI API request failed', data)
        self.assertNotIn('Invalid value', data)
        self.assertNotIn('400', data)

    @patch('architect.pathway_service.generate_architect_response')
    def test_original_provider_exception_is_logged_server_side(self, mock_ai):
        with app.app_context():
            pathway = self._pathway()
            user = User.query.filter_by(email='sme@example.com').first()

        class DummyOpenAIError(Exception):
            pass

        original = DummyOpenAIError('OpenAI API status 400 - invalid model for parse')
        ai_error = ArchitectAIError('OpenAI API request failed')
        ai_error.__cause__ = original

        mock_ai.side_effect = ai_error

        with self.assertLogs('architect.pathway_service', level='ERROR') as cm:
            with self.assertRaises(PathwayServiceError):
                with app.app_context():
                    process_architect_turn(pathway, user, 'Trigger a logged failure.')

        # The original provider-level exception must be visible in server logs.
        self.assertEqual(len(cm.output), 1)
        self.assertIn('Original Architect AI error before wrapping', cm.output[0])
        self.assertIn('OpenAI API status 400', cm.output[0])

    # --- PA-003.3 strict schema tests ---

    def test_architect_response_schema_has_additional_properties_false(self):
        from architect.schemas import ArchitectResponse
        schema = ArchitectResponse.model_json_schema()
        # Pydantic v2 places model defs under '$defs' and uses $ref for nested models.
        # The 'fields' object is ProposalFields, whose schema must have additionalProperties: false.
        fields_schema = schema['$defs']['ProposalFields']
        self.assertIn('additionalProperties', fields_schema)
        self.assertIs(fields_schema['additionalProperties'], False)

    def test_proposal_rejects_arbitrary_fields(self):
        from architect.schemas import Proposal
        with self.assertRaises(Exception):
            Proposal(operation='update_pathway', fields={'unknown_field': 'value'}, reason='Test.')

    def test_proposal_fields_dict_excludes_none_values(self):
        from architect.schemas import Proposal
        proposal = Proposal(operation='update_pathway', fields={'purpose': 'A clearer purpose.'}, reason='Test.')
        self.assertEqual(proposal.fields_dict.get('purpose'), 'A clearer purpose.')
        self.assertNotIn('outcome', proposal.fields_dict)


if __name__ == '__main__':
    unittest.main()
