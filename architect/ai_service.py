"""AI service boundary for the Pathway Architect."""
import json
import os

from openai import OpenAI, APIError

from .context import build_pathway_context
from .prompts import build_system_prompt
from .schemas import ArchitectResponse


class ArchitectAIError(Exception):
    """Raised when the Architect AI call or response parsing fails."""


def generate_architect_response(pathway, conversation_messages, user_content):
    """Call the configured AI model and return a validated ArchitectResponse.

    conversation_messages is a list of ArchitectMessage-like objects with
    `role` and `content` attributes (e.g., the prior messages in the turn).
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ArchitectAIError('OPENAI_API_KEY is not configured in the environment.')

    model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
    client = OpenAI(api_key=api_key)

    context = build_pathway_context(pathway)
    system_prompt = build_system_prompt(context)

    messages = [{'role': 'system', 'content': system_prompt}]
    for msg in conversation_messages:
        messages.append({'role': msg.role, 'content': msg.content})
    messages.append({'role': 'user', 'content': user_content})

    try:
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=ArchitectResponse,
            temperature=0.4,
        )
    except APIError as e:
        raise ArchitectAIError(f'AI API request failed: {e}') from e
    except Exception as e:
        raise ArchitectAIError(f'AI request failed: {e}') from e

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        # Fallback: attempt to parse the raw content if the structured parse is unavailable.
        raw = completion.choices[0].message.content
        if not raw:
            raise ArchitectAIError('AI returned an empty response.')
        try:
            parsed = ArchitectResponse.model_validate_json(raw)
        except Exception as e:
            raise ArchitectAIError(f'AI response did not match the required schema: {e}') from e

    return parsed
