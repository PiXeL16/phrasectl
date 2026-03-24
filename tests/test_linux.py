# ABOUTME: Tests for the Linux/Wayland platform implementation.
# ABOUTME: Validates wl-copy/wl-paste/wtype/hyprctl/notify-send subprocess interactions.

import json
import subprocess
from unittest.mock import MagicMock, patch


# --- Clipboard ---


def test_get_clipboard_calls_wl_paste():
    """get_clipboard calls wl-paste --no-newline and returns its stdout."""
    from phrasectl.linux import get_clipboard

    mock_result = MagicMock()
    mock_result.stdout = "hello world"
    mock_result.returncode = 0

    with patch("phrasectl.linux.subprocess.run", return_value=mock_result) as mock_run:
        result = get_clipboard()

    mock_run.assert_called_once_with(
        ["wl-paste", "--no-newline"], capture_output=True, text=True
    )
    assert result == "hello world"


def test_get_clipboard_returns_empty_on_failure():
    """get_clipboard returns empty string when wl-paste fails."""
    from phrasectl.linux import get_clipboard

    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_result.returncode = 1

    with patch("phrasectl.linux.subprocess.run", return_value=mock_result):
        result = get_clipboard()

    assert result == ""


def test_set_clipboard_pipes_to_wl_copy():
    """set_clipboard pipes text to wl-copy via stdin."""
    from phrasectl.linux import set_clipboard

    mock_proc = MagicMock()
    mock_proc.communicate = MagicMock()

    with patch("phrasectl.linux.subprocess.Popen", return_value=mock_proc) as mock_popen:
        set_clipboard("rephrased text")

    mock_popen.assert_called_once_with(["wl-copy"], stdin=subprocess.PIPE)
    mock_proc.communicate.assert_called_once_with(input=b"rephrased text")


# --- Keyboard ---


def test_send_copy_gui_app():
    """send_copy sends Ctrl+C via wtype for GUI apps."""
    from phrasectl.linux import send_copy

    with patch("phrasectl.linux.subprocess.run") as mock_run:
        send_copy(is_terminal=False)

    mock_run.assert_called_once_with(
        ["wtype", "-M", "ctrl", "-k", "c", "-m", "ctrl"],
        check=True,
    )


def test_send_copy_terminal():
    """send_copy sends Ctrl+Shift+C via wtype for terminal apps."""
    from phrasectl.linux import send_copy

    with patch("phrasectl.linux.subprocess.run") as mock_run:
        send_copy(is_terminal=True)

    mock_run.assert_called_once_with(
        ["wtype", "-M", "ctrl", "-M", "shift", "-k", "c", "-m", "shift", "-m", "ctrl"],
        check=True,
    )


def test_send_paste_gui_app():
    """send_paste sends Ctrl+V via wtype for GUI apps."""
    from phrasectl.linux import send_paste

    with patch("phrasectl.linux.subprocess.run") as mock_run:
        send_paste(is_terminal=False)

    mock_run.assert_called_once_with(
        ["wtype", "-M", "ctrl", "-k", "v", "-m", "ctrl"],
        check=True,
    )


def test_send_paste_terminal():
    """send_paste sends Ctrl+Shift+V via wtype for terminal apps."""
    from phrasectl.linux import send_paste

    with patch("phrasectl.linux.subprocess.run") as mock_run:
        send_paste(is_terminal=True)

    mock_run.assert_called_once_with(
        ["wtype", "-M", "ctrl", "-M", "shift", "-k", "v", "-m", "shift", "-m", "ctrl"],
        check=True,
    )


def test_send_select_all():
    """send_select_all sends Ctrl+A via wtype."""
    from phrasectl.linux import send_select_all

    with patch("phrasectl.linux.subprocess.run") as mock_run:
        send_select_all()

    mock_run.assert_called_once_with(
        ["wtype", "-M", "ctrl", "-k", "a", "-m", "ctrl"],
        check=True,
    )


# --- Window detection ---


def _make_hyprctl_result(window_class: str) -> MagicMock:
    """Helper to create a mock hyprctl activewindow -j result."""
    mock_result = MagicMock()
    mock_result.stdout = json.dumps({"class": window_class, "title": "test"})
    mock_result.returncode = 0
    return mock_result


def test_get_active_window_class_parses_hyprctl_json():
    """get_active_window_class returns the class from hyprctl activewindow JSON."""
    from phrasectl.linux import get_active_window_class

    mock_result = _make_hyprctl_result("zen-browser")

    with patch("phrasectl.linux.subprocess.run", return_value=mock_result) as mock_run:
        result = get_active_window_class()

    mock_run.assert_called_once_with(
        ["hyprctl", "activewindow", "-j"], capture_output=True, text=True
    )
    assert result == "zen-browser"


def test_get_active_window_class_returns_empty_on_error():
    """get_active_window_class returns empty string when hyprctl fails."""
    from phrasectl.linux import get_active_window_class

    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_result.returncode = 1

    with patch("phrasectl.linux.subprocess.run", return_value=mock_result):
        result = get_active_window_class()

    assert result == ""


def test_detect_terminal_ghostty():
    """detect_terminal returns True for Ghostty."""
    from phrasectl.linux import detect_terminal

    assert detect_terminal("com.mitchellh.ghostty") is True


def test_detect_terminal_kitty():
    """detect_terminal returns True for kitty."""
    from phrasectl.linux import detect_terminal

    assert detect_terminal("kitty") is True


def test_detect_terminal_alacritty():
    """detect_terminal returns True for Alacritty."""
    from phrasectl.linux import detect_terminal

    assert detect_terminal("Alacritty") is True


def test_detect_terminal_false_for_browser():
    """detect_terminal returns False for non-terminal apps."""
    from phrasectl.linux import detect_terminal

    assert detect_terminal("zen-browser") is False


def test_detect_terminal_false_for_empty():
    """detect_terminal returns False for empty string."""
    from phrasectl.linux import detect_terminal

    assert detect_terminal("") is False


# --- Notifications ---


def test_notify_calls_notify_send():
    """notify shells out to notify-send with correct args."""
    from phrasectl.linux import notify

    with patch("phrasectl.linux.subprocess.run") as mock_run:
        notify("Rephrase", "Done!")

    mock_run.assert_called_once_with(
        ["notify-send", "--app-name=phrasectl", "--expire-time=3000", "Rephrase", "Done!"]
    )


def test_notify_skipped_when_disabled():
    """notify does nothing when notifications are disabled."""
    from phrasectl.linux import notify

    with patch("phrasectl.linux.subprocess.run") as mock_run:
        notify("Title", "Body", enabled=False)

    mock_run.assert_not_called()
