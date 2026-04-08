# ABOUTME: Tests for the main orchestration flow and CLI argument handling.
# ABOUTME: Covers end-to-end flow, error handling, and profile listing.

from unittest.mock import MagicMock, call, patch


def _make_mock_platform():
    """Create a mock platform module with all required functions."""
    platform = MagicMock()
    platform.get_clipboard = MagicMock()
    platform.set_clipboard = MagicMock()
    platform.send_copy = MagicMock()
    platform.send_paste = MagicMock()
    platform.send_select_all = MagicMock()
    platform.get_active_window_class = MagicMock(return_value="test-app")
    platform.detect_terminal = MagicMock(return_value=False)
    platform.notify = MagicMock()
    platform.MODIFIER_RELEASE_DELAY = 0.5
    platform.COPY_DELAY = 0.5
    platform.SENTINEL_DELAY = 0.1
    platform.SELECT_ALL_DELAY = 0.3
    platform.PASTE_DELAY = 0.3
    platform.RESTORE_DELAY = 0.5
    platform.COPY_SENTINEL = "__phrasectl_awaiting_copy__"
    return platform


def test_main_flow_happy_path():
    """Full flow: copy -> read clipboard -> rephrase -> write clipboard -> paste -> restore."""
    from phrasectl.__main__ import main
    from phrasectl.config import ApiConfig, BehaviorConfig, Config, Profile

    mock_platform = _make_mock_platform()
    mock_platform.get_clipboard.side_effect = ["original clipboard", "selected text"]

    mock_config = Config(
        api=ApiConfig(key="sk-test"),
        behavior=BehaviorConfig(
            default_profile="fix", notifications=True, restore_clipboard=True
        ),
        profiles={"fix": Profile(name="Fix", system_prompt="Fix.")},
    )

    with (
        patch("phrasectl.__main__.load_config", return_value=mock_config),
        patch("phrasectl.__main__.resolve_api_key", return_value="sk-test"),
        patch("phrasectl.__main__.get_platform", return_value=mock_platform),
        patch("phrasectl.__main__.rephrase_text", return_value="rephrased text"),
        patch("phrasectl.__main__.time.sleep"),
    ):
        main(["--profile", "fix", "--config", "/fake/config.toml"])

    # Should set clipboard to rephrased text, then restore original
    set_calls = mock_platform.set_clipboard.call_args_list
    assert call("rephrased text") in set_calls
    assert call("original clipboard") in set_calls

    # Should have notified about rephrasing and done
    notify_calls = [c[0] for c in mock_platform.notify.call_args_list]
    assert any("Rephras" in str(c) for c in notify_calls)
    assert any("Done" in str(c) for c in notify_calls)


def test_main_flow_no_selection_falls_back_to_select_all():
    """When clipboard still has sentinel after copy, select all then copy and rephrase."""
    from phrasectl.__main__ import main
    from phrasectl.config import ApiConfig, BehaviorConfig, Config, Profile

    mock_platform = _make_mock_platform()
    mock_platform.get_clipboard.side_effect = [
        "original",
        mock_platform.COPY_SENTINEL,
        "all the text",
    ]

    mock_config = Config(
        api=ApiConfig(key="sk-test"),
        behavior=BehaviorConfig(default_profile="fix", restore_clipboard=False),
        profiles={"fix": Profile(name="Fix", system_prompt="Fix.")},
    )

    with (
        patch("phrasectl.__main__.load_config", return_value=mock_config),
        patch("phrasectl.__main__.resolve_api_key", return_value="sk-test"),
        patch("phrasectl.__main__.get_platform", return_value=mock_platform),
        patch("phrasectl.__main__.rephrase_text", return_value="rephrased all") as mock_rephrase,
        patch("phrasectl.__main__.time.sleep"),
    ):
        main(["--profile", "fix", "--config", "/fake/config.toml"])

    # Should have called select all after first copy failed
    mock_platform.send_select_all.assert_called_once()
    # Should have called copy twice (initial attempt + after select all)
    assert mock_platform.send_copy.call_count == 2
    # Should have rephrased the text from select all
    mock_rephrase.assert_called_once()


def test_main_flow_no_selection_and_select_all_empty():
    """When both copy and select-all+copy find nothing, notify and restore clipboard."""
    from phrasectl.__main__ import main
    from phrasectl.config import ApiConfig, BehaviorConfig, Config, Profile

    mock_platform = _make_mock_platform()
    sentinel = mock_platform.COPY_SENTINEL
    mock_platform.get_clipboard.side_effect = [
        "original clipboard",
        sentinel,
        sentinel,
    ]

    mock_config = Config(
        api=ApiConfig(key="sk-test"),
        behavior=BehaviorConfig(default_profile="fix"),
        profiles={"fix": Profile(name="Fix", system_prompt="Fix.")},
    )

    with (
        patch("phrasectl.__main__.load_config", return_value=mock_config),
        patch("phrasectl.__main__.resolve_api_key", return_value="sk-test"),
        patch("phrasectl.__main__.get_platform", return_value=mock_platform),
        patch("phrasectl.__main__.rephrase_text") as mock_rephrase,
        patch("phrasectl.__main__.time.sleep"),
    ):
        main(["--profile", "fix", "--config", "/fake/config.toml"])

    # Should NOT have called rephrase or paste
    mock_rephrase.assert_not_called()
    mock_platform.send_paste.assert_not_called()

    # Should notify about no selection
    notify_calls = [str(c) for c in mock_platform.notify.call_args_list]
    assert any("No text selected" in c for c in notify_calls)

    # Should restore original clipboard (we clobbered it with sentinel)
    set_calls = mock_platform.set_clipboard.call_args_list
    assert call("original clipboard") in set_calls


def test_main_flow_no_api_key():
    """When no API key is available, notify and exit without calling the API."""
    from phrasectl.__main__ import main
    from phrasectl.config import ApiConfig, BehaviorConfig, Config, Profile

    mock_platform = _make_mock_platform()

    mock_config = Config(
        api=ApiConfig(key=""),
        behavior=BehaviorConfig(default_profile="fix"),
        profiles={"fix": Profile(name="Fix", system_prompt="Fix.")},
    )

    with (
        patch("phrasectl.__main__.load_config", return_value=mock_config),
        patch("phrasectl.__main__.resolve_api_key", return_value=None),
        patch("phrasectl.__main__.get_platform", return_value=mock_platform),
        patch("phrasectl.__main__.rephrase_text") as mock_rephrase,
        patch("phrasectl.__main__.time.sleep"),
    ):
        main(["--config", "/fake/config.toml"])

    mock_rephrase.assert_not_called()
    mock_platform.send_copy.assert_not_called()

    notify_calls = [str(c) for c in mock_platform.notify.call_args_list]
    assert any("API key" in c for c in notify_calls)


def test_main_flow_api_error_restores_clipboard():
    """When the API call fails, notify the error and restore the original clipboard."""
    from phrasectl.__main__ import main
    from phrasectl.config import ApiConfig, BehaviorConfig, Config, Profile

    mock_platform = _make_mock_platform()
    mock_platform.get_clipboard.side_effect = ["original", "selected text"]

    mock_config = Config(
        api=ApiConfig(key="sk-test"),
        behavior=BehaviorConfig(
            default_profile="fix", restore_clipboard=True
        ),
        profiles={"fix": Profile(name="Fix", system_prompt="Fix.")},
    )

    with (
        patch("phrasectl.__main__.load_config", return_value=mock_config),
        patch("phrasectl.__main__.resolve_api_key", return_value="sk-test"),
        patch("phrasectl.__main__.get_platform", return_value=mock_platform),
        patch("phrasectl.__main__.rephrase_text", side_effect=Exception("API timeout")),
        patch("phrasectl.__main__.time.sleep"),
    ):
        main(["--config", "/fake/config.toml"])

    # Should NOT paste
    mock_platform.send_paste.assert_not_called()

    # Should restore original clipboard (sentinel + restore = 2 calls)
    set_calls = mock_platform.set_clipboard.call_args_list
    assert call("original") in set_calls

    # Should notify about error
    notify_calls = [str(c) for c in mock_platform.notify.call_args_list]
    assert any("Error" in c or "error" in c or "API timeout" in c for c in notify_calls)


def test_main_list_profiles(capsys):
    """--list-profiles prints available profiles and exits."""
    from phrasectl.__main__ import main
    from phrasectl.config import ApiConfig, BehaviorConfig, Config, Profile

    mock_config = Config(
        api=ApiConfig(),
        behavior=BehaviorConfig(default_profile="fix"),
        profiles={
            "fix": Profile(name="Fix Grammar", system_prompt="Fix."),
            "formal": Profile(name="Make Formal", system_prompt="Formal."),
        },
    )

    with patch("phrasectl.__main__.load_config", return_value=mock_config):
        main(["--list-profiles", "--config", "/fake/config.toml"])

    captured = capsys.readouterr()
    assert "fix" in captured.out
    assert "Fix Grammar" in captured.out
    assert "formal" in captured.out
    assert "Make Formal" in captured.out


def test_main_flow_no_clipboard_restore():
    """When restore_clipboard is False, don't restore the original clipboard."""
    from phrasectl.__main__ import main
    from phrasectl.config import ApiConfig, BehaviorConfig, Config, Profile

    mock_platform = _make_mock_platform()
    mock_platform.get_clipboard.side_effect = ["original", "selected"]

    mock_config = Config(
        api=ApiConfig(key="sk-test"),
        behavior=BehaviorConfig(
            default_profile="fix", restore_clipboard=False
        ),
        profiles={"fix": Profile(name="Fix", system_prompt="Fix.")},
    )

    with (
        patch("phrasectl.__main__.load_config", return_value=mock_config),
        patch("phrasectl.__main__.resolve_api_key", return_value="sk-test"),
        patch("phrasectl.__main__.get_platform", return_value=mock_platform),
        patch("phrasectl.__main__.rephrase_text", return_value="rephrased"),
        patch("phrasectl.__main__.time.sleep"),
    ):
        main(["--config", "/fake/config.toml"])

    # Should set clipboard with sentinel + rephrased text, but NOT restore original
    set_calls = mock_platform.set_clipboard.call_args_list
    assert call("rephrased") in set_calls
    assert call("original") not in set_calls
