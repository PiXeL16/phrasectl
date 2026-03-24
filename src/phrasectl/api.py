# ABOUTME: Claude API integration for text rephrasing.
# ABOUTME: Handles Anthropic client creation and message submission.

from __future__ import annotations

import anthropic

from phrasectl.config import Config, Profile
from phrasectl.prompt import build_messages, get_system_prompt


def rephrase_text(config: Config, profile: Profile, text: str) -> str:
    """Send text to the Claude API for rephrasing and return the result."""
    api_key = config.api.key or None
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=config.api.model,
        max_tokens=config.api.max_tokens,
        system=get_system_prompt(profile),
        messages=build_messages(text),
    )
    return message.content[0].text
