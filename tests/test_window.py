# ABOUTME: Tests for active window detection and terminal class identification.
# ABOUTME: Validates hyprctl JSON parsing and terminal detection logic.

import json
from unittest.mock import patch, MagicMock


def _make_hyprctl_result(window_class: str) -> MagicMock:
    """Helper to create a mock hyprctl activewindow -j result."""
    mock_result = MagicMock()
    mock_result.stdout = json.dumps({"class": window_class, "title": "test"})
    mock_result.returncode = 0
    return mock_result


def test_get_active_window_class_parses_hyprctl_json():
    """get_active_window_class returns the class from hyprctl activewindow JSON."""
    from phrasectl import get_active_window_class

    mock_result = _make_hyprctl_result("zen-browser")

    with patch("phrasectl.subprocess.run", return_value=mock_result) as mock_run:
        result = get_active_window_class()

    mock_run.assert_called_once_with(
        ["hyprctl", "activewindow", "-j"], capture_output=True, text=True
    )
    assert result == "zen-browser"


def test_get_active_window_class_returns_empty_on_error():
    """get_active_window_class returns empty string when hyprctl fails."""
    from phrasectl import get_active_window_class

    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_result.returncode = 1

    with patch("phrasectl.subprocess.run", return_value=mock_result):
        result = get_active_window_class()

    assert result == ""


def test_detect_terminal_ghostty():
    """detect_terminal returns True for Ghostty."""
    from phrasectl import detect_terminal

    assert detect_terminal("com.mitchellh.ghostty") is True


def test_detect_terminal_kitty():
    """detect_terminal returns True for kitty."""
    from phrasectl import detect_terminal

    assert detect_terminal("kitty") is True


def test_detect_terminal_alacritty():
    """detect_terminal returns True for Alacritty."""
    from phrasectl import detect_terminal

    assert detect_terminal("Alacritty") is True


def test_detect_terminal_false_for_browser():
    """detect_terminal returns False for non-terminal apps."""
    from phrasectl import detect_terminal

    assert detect_terminal("zen-browser") is False


def test_detect_terminal_false_for_empty():
    """detect_terminal returns False for empty string."""
    from phrasectl import detect_terminal

    assert detect_terminal("") is False
