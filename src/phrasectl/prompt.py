# ABOUTME: Prompt construction helpers for the Claude API.
# ABOUTME: Builds message lists and extracts system prompts from profiles.

from __future__ import annotations

from phrasectl.config import Profile


def get_system_prompt(profile: Profile) -> str:
    """Extract the system prompt string from a profile."""
    return profile.system_prompt


def build_messages(text: str) -> list[dict[str, str]]:
    """Build the messages list for the Claude API from user text."""
    return [{"role": "user", "content": text}]
