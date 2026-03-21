# ABOUTME: Tests for prompt construction and message formatting for the Claude API.
# ABOUTME: Validates that profiles produce correct system prompts and user messages.


def test_build_messages_returns_user_text():
    """build_messages wraps the input text as a user message."""
    from phrasectl import build_messages

    messages = build_messages("hello wrold")
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "hello wrold"


def test_build_messages_preserves_whitespace():
    """build_messages preserves leading/trailing whitespace and newlines."""
    from phrasectl import build_messages

    text = "  hello\n  world  "
    messages = build_messages(text)
    assert messages[0]["content"] == text


def test_get_system_prompt_from_profile():
    """get_system_prompt extracts the system_prompt string from a Profile."""
    from phrasectl import Profile, get_system_prompt

    profile = Profile(name="Test", system_prompt="You are a helpful editor.")
    assert get_system_prompt(profile) == "You are a helpful editor."


def test_get_system_prompt_multiline():
    """get_system_prompt works with multiline system prompts."""
    from phrasectl import Profile, get_system_prompt

    prompt = "Line one.\nLine two.\nLine three."
    profile = Profile(name="Multi", system_prompt=prompt)
    assert get_system_prompt(profile) == prompt
