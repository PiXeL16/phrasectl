# ABOUTME: Tests for the core rephrasing logic, API call, main orchestration flow, and CLI.
# ABOUTME: Covers API interaction, error handling, notification calls, and end-to-end flow.

import subprocess
from unittest.mock import MagicMock, call, patch

import pytest


# --- API call tests ---


def test_rephrase_text_calls_anthropic_api():
    """rephrase_text creates an Anthropic client and calls messages.create."""
    from phrasectl import ApiConfig, Config, Profile, rephrase_text

    config = Config(api=ApiConfig(key="sk-test", model="claude-sonnet-4-6", max_tokens=2048))
    profile = Profile(name="Fix", system_prompt="Fix the text.")

    mock_content = MagicMock()
    mock_content.text = "fixed text"
    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("phrasectl.anthropic.Anthropic", return_value=mock_client):
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
    from phrasectl import ApiConfig, Config, Profile, rephrase_text

    config = Config(api=ApiConfig(key="", model="claude-sonnet-4-6", max_tokens=4096))
    profile = Profile(name="Fix", system_prompt="Fix.")

    mock_content = MagicMock()
    mock_content.text = "result"
    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("phrasectl.anthropic.Anthropic", return_value=mock_client) as mock_cls:
        rephrase_text(config, profile, "input")

    # When key is empty, pass None so SDK picks up ANTHROPIC_API_KEY env var
    mock_cls.assert_called_once_with(api_key=None)


# --- Notification tests ---


def test_notify_calls_notify_send():
    """notify shells out to notify-send with correct args."""
    from phrasectl import notify

    with patch("phrasectl.subprocess.run") as mock_run:
        notify("Repharse", "Done!")

    mock_run.assert_called_once_with(
        ["notify-send", "--app-name=phrasectl", "--expire-time=3000", "Repharse", "Done!"]
    )


def test_notify_skipped_when_disabled():
    """notify does nothing when notifications are disabled."""
    from phrasectl import notify

    with patch("phrasectl.subprocess.run") as mock_run:
        notify("Title", "Body", enabled=False)

    mock_run.assert_not_called()


# --- Main flow tests ---


def test_main_flow_happy_path():
    """Full flow: copy → read clipboard → rephrase → write clipboard → paste → restore."""
    from phrasectl import main

    with (
        patch("phrasectl.load_config") as mock_load_config,
        patch("phrasectl.resolve_api_key", return_value="sk-test"),
        patch("phrasectl.get_clipboard", side_effect=["original clipboard", "selected text"]),
        patch("phrasectl.send_copy"),
        patch("phrasectl.set_clipboard") as mock_set_clipboard,
        patch("phrasectl.send_paste"),
        patch("phrasectl.notify") as mock_notify,
        patch("phrasectl.rephrase_text", return_value="rephrased text"),
        patch("phrasectl.time.sleep"),
    ):
        from phrasectl import (
            ApiConfig,
            BehaviorConfig,
            Config,
            Profile,
        )

        mock_load_config.return_value = Config(
            api=ApiConfig(key="sk-test"),
            behavior=BehaviorConfig(
                default_profile="fix", notifications=True, restore_clipboard=True
            ),
            profiles={"fix": Profile(name="Fix", system_prompt="Fix.")},
        )

        main(["--profile", "fix", "--config", "/fake/config.toml"])

    # Should set clipboard to rephrased text, then restore original
    set_calls = mock_set_clipboard.call_args_list
    assert call("rephrased text") in set_calls
    assert call("original clipboard") in set_calls

    # Should have notified about rephrasing and done
    notify_calls = [c[0] for c in mock_notify.call_args_list]
    assert any("Rephras" in str(c) for c in notify_calls)
    assert any("Done" in str(c) for c in notify_calls)


def test_main_flow_no_selection_falls_back_to_select_all():
    """When clipboard doesn't change after copy, select all then copy and rephrase."""
    from phrasectl import main

    with (
        patch("phrasectl.load_config") as mock_load_config,
        patch("phrasectl.resolve_api_key", return_value="sk-test"),
        patch("phrasectl.get_clipboard", side_effect=["original", "original", "all the text"]),
        patch("phrasectl.send_copy") as mock_send_copy,
        patch("phrasectl.send_select_all") as mock_select_all,
        patch("phrasectl.set_clipboard") as mock_set_clipboard,
        patch("phrasectl.send_paste"),
        patch("phrasectl.notify"),
        patch("phrasectl.rephrase_text", return_value="rephrased all") as mock_rephrase,
        patch("phrasectl.time.sleep"),
    ):
        from phrasectl import (
            ApiConfig,
            BehaviorConfig,
            Config,
            Profile,
        )

        mock_load_config.return_value = Config(
            api=ApiConfig(key="sk-test"),
            behavior=BehaviorConfig(default_profile="fix", restore_clipboard=False),
            profiles={"fix": Profile(name="Fix", system_prompt="Fix.")},
        )

        main(["--profile", "fix", "--config", "/fake/config.toml"])

    # Should have called select all after first copy failed
    mock_select_all.assert_called_once()
    # Should have called copy twice (initial attempt + after select all)
    assert mock_send_copy.call_count == 2
    # Should have rephrased the text from select all
    mock_rephrase.assert_called_once()


def test_main_flow_no_selection_and_select_all_empty():
    """When both copy and select-all+copy find nothing, notify and exit."""
    from phrasectl import main

    with (
        patch("phrasectl.load_config") as mock_load_config,
        patch("phrasectl.resolve_api_key", return_value="sk-test"),
        patch("phrasectl.get_clipboard", return_value="same clipboard"),
        patch("phrasectl.send_copy"),
        patch("phrasectl.send_select_all"),
        patch("phrasectl.set_clipboard") as mock_set_clipboard,
        patch("phrasectl.send_paste") as mock_send_paste,
        patch("phrasectl.notify") as mock_notify,
        patch("phrasectl.rephrase_text") as mock_rephrase,
        patch("phrasectl.time.sleep"),
    ):
        from phrasectl import (
            ApiConfig,
            BehaviorConfig,
            Config,
            Profile,
        )

        mock_load_config.return_value = Config(
            api=ApiConfig(key="sk-test"),
            behavior=BehaviorConfig(default_profile="fix"),
            profiles={"fix": Profile(name="Fix", system_prompt="Fix.")},
        )

        main(["--profile", "fix", "--config", "/fake/config.toml"])

    # Should NOT have called rephrase or paste
    mock_rephrase.assert_not_called()
    mock_send_paste.assert_not_called()

    # Should notify about no selection
    notify_calls = [str(c) for c in mock_notify.call_args_list]
    assert any("No text selected" in c for c in notify_calls)


def test_main_flow_no_api_key():
    """When no API key is available, notify and exit without calling the API."""
    from phrasectl import main

    with (
        patch("phrasectl.load_config") as mock_load_config,
        patch("phrasectl.resolve_api_key", return_value=None),
        patch("phrasectl.get_clipboard") as mock_get_clipboard,
        patch("phrasectl.send_copy") as mock_send_copy,
        patch("phrasectl.notify") as mock_notify,
        patch("phrasectl.rephrase_text") as mock_rephrase,
        patch("phrasectl.time.sleep"),
    ):
        from phrasectl import (
            ApiConfig,
            BehaviorConfig,
            Config,
            Profile,
        )

        mock_load_config.return_value = Config(
            api=ApiConfig(key=""),
            behavior=BehaviorConfig(default_profile="fix"),
            profiles={"fix": Profile(name="Fix", system_prompt="Fix.")},
        )

        main(["--config", "/fake/config.toml"])

    mock_rephrase.assert_not_called()
    mock_send_copy.assert_not_called()

    notify_calls = [str(c) for c in mock_notify.call_args_list]
    assert any("API key" in c for c in notify_calls)


def test_main_flow_api_error_restores_clipboard():
    """When the API call fails, notify the error and restore the original clipboard."""
    from phrasectl import main

    with (
        patch("phrasectl.load_config") as mock_load_config,
        patch("phrasectl.resolve_api_key", return_value="sk-test"),
        patch("phrasectl.get_clipboard", side_effect=["original", "selected text"]),
        patch("phrasectl.send_copy"),
        patch("phrasectl.set_clipboard") as mock_set_clipboard,
        patch("phrasectl.send_paste") as mock_send_paste,
        patch("phrasectl.notify") as mock_notify,
        patch("phrasectl.rephrase_text", side_effect=Exception("API timeout")),
        patch("phrasectl.time.sleep"),
    ):
        from phrasectl import (
            ApiConfig,
            BehaviorConfig,
            Config,
            Profile,
        )

        mock_load_config.return_value = Config(
            api=ApiConfig(key="sk-test"),
            behavior=BehaviorConfig(
                default_profile="fix", restore_clipboard=True
            ),
            profiles={"fix": Profile(name="Fix", system_prompt="Fix.")},
        )

        main(["--config", "/fake/config.toml"])

    # Should NOT paste
    mock_send_paste.assert_not_called()

    # Should restore original clipboard
    mock_set_clipboard.assert_called_once_with("original")

    # Should notify about error
    notify_calls = [str(c) for c in mock_notify.call_args_list]
    assert any("Error" in c or "error" in c or "API timeout" in c for c in notify_calls)


def test_main_list_profiles(capsys):
    """--list-profiles prints available profiles and exits."""
    from phrasectl import main

    with patch("phrasectl.load_config") as mock_load_config:
        from phrasectl import (
            ApiConfig,
            BehaviorConfig,
            Config,
            Profile,
        )

        mock_load_config.return_value = Config(
            api=ApiConfig(),
            behavior=BehaviorConfig(default_profile="fix"),
            profiles={
                "fix": Profile(name="Fix Grammar", system_prompt="Fix."),
                "formal": Profile(name="Make Formal", system_prompt="Formal."),
            },
        )

        main(["--list-profiles", "--config", "/fake/config.toml"])

    captured = capsys.readouterr()
    assert "fix" in captured.out
    assert "Fix Grammar" in captured.out
    assert "formal" in captured.out
    assert "Make Formal" in captured.out


def test_main_flow_no_clipboard_restore():
    """When restore_clipboard is False, don't restore the original clipboard."""
    from phrasectl import main

    with (
        patch("phrasectl.load_config") as mock_load_config,
        patch("phrasectl.resolve_api_key", return_value="sk-test"),
        patch("phrasectl.get_clipboard", side_effect=["original", "selected"]),
        patch("phrasectl.send_copy"),
        patch("phrasectl.set_clipboard") as mock_set_clipboard,
        patch("phrasectl.send_paste"),
        patch("phrasectl.notify"),
        patch("phrasectl.rephrase_text", return_value="rephrased"),
        patch("phrasectl.time.sleep"),
    ):
        from phrasectl import (
            ApiConfig,
            BehaviorConfig,
            Config,
            Profile,
        )

        mock_load_config.return_value = Config(
            api=ApiConfig(key="sk-test"),
            behavior=BehaviorConfig(
                default_profile="fix", restore_clipboard=False
            ),
            profiles={"fix": Profile(name="Fix", system_prompt="Fix.")},
        )

        main(["--config", "/fake/config.toml"])

    # Should only set clipboard once (the rephrased text), not restore
    mock_set_clipboard.assert_called_once_with("rephrased")
