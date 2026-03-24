# ABOUTME: Tests for the Claude API integration layer.
# ABOUTME: Validates Anthropic client creation, message submission, and API key handling.

from unittest.mock import MagicMock, patch


def test_rephrase_text_calls_anthropic_api():
    """rephrase_text creates an Anthropic client and calls messages.create."""
    from phrasectl.api import rephrase_text
    from phrasectl.config import ApiConfig, Config, Profile

    config = Config(api=ApiConfig(key="sk-test", model="claude-sonnet-4-6", max_tokens=2048))
    profile = Profile(name="Fix", system_prompt="Fix the text.")

    mock_content = MagicMock()
    mock_content.text = "fixed text"
    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("phrasectl.api.anthropic.Anthropic", return_value=mock_client):
        result = rephrase_text(config, profile, "broken text")

    mock_client.messages.create.assert_called_once_with(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system="Fix the text.",
        messages=[{"role": "user", "content": "broken text"}],
    )
    assert result == "fixed text"


def test_rephrase_text_uses_env_key_when_config_key_empty():
    """rephrase_text passes api_key=None when config key is empty (SDK uses env var)."""
    from phrasectl.api import rephrase_text
    from phrasectl.config import ApiConfig, Config, Profile

    config = Config(api=ApiConfig(key="", model="claude-sonnet-4-6", max_tokens=4096))
    profile = Profile(name="Fix", system_prompt="Fix.")

    mock_content = MagicMock()
    mock_content.text = "result"
    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("phrasectl.api.anthropic.Anthropic", return_value=mock_client) as mock_cls:
        rephrase_text(config, profile, "input")

    # When key is empty, pass None so SDK picks up ANTHROPIC_API_KEY env var
    mock_cls.assert_called_once_with(api_key=None)
