# ABOUTME: Tests for the macOS platform implementation.
# ABOUTME: Validates pbcopy/pbpaste/osascript subprocess interactions.

import subprocess
from unittest.mock import MagicMock, patch


# --- Clipboard ---


def test_get_clipboard_calls_pbpaste():
    """get_clipboard calls pbpaste and returns its stdout."""
    from phrasectl.macos import get_clipboard

    mock_result = MagicMock()
    mock_result.stdout = "hello world"
    mock_result.returncode = 0

    with patch("phrasectl.macos.subprocess.run", return_value=mock_result) as mock_run:
        result = get_clipboard()

    mock_run.assert_called_once_with(
        ["pbpaste"], capture_output=True, text=True
    )
    assert result == "hello world"


def test_get_clipboard_returns_empty_on_failure():
    """get_clipboard returns empty string when pbpaste fails."""
    from phrasectl.macos import get_clipboard

    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_result.returncode = 1

    with patch("phrasectl.macos.subprocess.run", return_value=mock_result):
        result = get_clipboard()

    assert result == ""


def test_set_clipboard_pipes_to_pbcopy():
    """set_clipboard pipes text to pbcopy via stdin."""
    from phrasectl.macos import set_clipboard

    mock_proc = MagicMock()
    mock_proc.communicate = MagicMock()

    with patch("phrasectl.macos.subprocess.Popen", return_value=mock_proc) as mock_popen:
        set_clipboard("rephrased text")

    mock_popen.assert_called_once_with(["pbcopy"], stdin=subprocess.PIPE)
    mock_proc.communicate.assert_called_once_with(input=b"rephrased text")


# --- Keyboard ---


def test_send_copy_uses_osascript_cmd_c():
    """send_copy sends Cmd+C via osascript regardless of is_terminal."""
    from phrasectl.macos import send_copy

    with patch("phrasectl.macos.subprocess.run") as mock_run:
        send_copy(is_terminal=False)

    mock_run.assert_called_once_with(
        ["osascript", "-e", 'tell application "System Events" to keystroke "c" using command down'],
        check=True,
    )


def test_send_copy_ignores_is_terminal():
    """send_copy sends the same Cmd+C for terminal apps on macOS."""
    from phrasectl.macos import send_copy

    with patch("phrasectl.macos.subprocess.run") as mock_run:
        send_copy(is_terminal=True)

    mock_run.assert_called_once_with(
        ["osascript", "-e", 'tell application "System Events" to keystroke "c" using command down'],
        check=True,
    )


def test_send_paste_uses_osascript_cmd_v():
    """send_paste sends Cmd+V via osascript."""
    from phrasectl.macos import send_paste

    with patch("phrasectl.macos.subprocess.run") as mock_run:
        send_paste(is_terminal=False)

    mock_run.assert_called_once_with(
        ["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down'],
        check=True,
    )


def test_send_paste_ignores_is_terminal():
    """send_paste sends the same Cmd+V for terminal apps on macOS."""
    from phrasectl.macos import send_paste

    with patch("phrasectl.macos.subprocess.run") as mock_run:
        send_paste(is_terminal=True)

    mock_run.assert_called_once_with(
        ["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down'],
        check=True,
    )


def test_send_select_all_uses_osascript_cmd_a():
    """send_select_all sends Cmd+A via osascript."""
    from phrasectl.macos import send_select_all

    with patch("phrasectl.macos.subprocess.run") as mock_run:
        send_select_all()

    mock_run.assert_called_once_with(
        ["osascript", "-e", 'tell application "System Events" to keystroke "a" using command down'],
        check=True,
    )


# --- Window detection ---


def test_get_active_window_class_returns_app_name():
    """get_active_window_class returns the frontmost app name via osascript."""
    from phrasectl.macos import get_active_window_class

    mock_result = MagicMock()
    mock_result.stdout = "Safari\n"
    mock_result.returncode = 0

    with patch("phrasectl.macos.subprocess.run", return_value=mock_result) as mock_run:
        result = get_active_window_class()

    mock_run.assert_called_once_with(
        ["osascript", "-e",
         'tell application "System Events" to get name of first application process whose frontmost is true'],
        capture_output=True, text=True,
    )
    assert result == "Safari"


def test_get_active_window_class_returns_empty_on_error():
    """get_active_window_class returns empty string when osascript fails."""
    from phrasectl.macos import get_active_window_class

    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_result.returncode = 1

    with patch("phrasectl.macos.subprocess.run", return_value=mock_result):
        result = get_active_window_class()

    assert result == ""


def test_detect_terminal_iterm2():
    """detect_terminal returns True for iTerm2."""
    from phrasectl.macos import detect_terminal

    assert detect_terminal("iTerm2") is True


def test_detect_terminal_terminal_app():
    """detect_terminal returns True for Terminal."""
    from phrasectl.macos import detect_terminal

    assert detect_terminal("Terminal") is True


def test_detect_terminal_ghostty():
    """detect_terminal returns True for Ghostty."""
    from phrasectl.macos import detect_terminal

    assert detect_terminal("Ghostty") is True


def test_detect_terminal_false_for_safari():
    """detect_terminal returns False for non-terminal apps."""
    from phrasectl.macos import detect_terminal

    assert detect_terminal("Safari") is False


def test_detect_terminal_false_for_empty():
    """detect_terminal returns False for empty string."""
    from phrasectl.macos import detect_terminal

    assert detect_terminal("") is False


# --- Notifications ---


def test_notify_calls_osascript():
    """notify shows notification via osascript."""
    from phrasectl.macos import notify

    with patch("phrasectl.macos.subprocess.run") as mock_run:
        notify("Rephrase", "Done!")

    mock_run.assert_called_once_with(
        ["osascript", "-e",
         'display notification "Done!" with title "Rephrase"']
    )


def test_notify_skipped_when_disabled():
    """notify does nothing when notifications are disabled."""
    from phrasectl.macos import notify

    with patch("phrasectl.macos.subprocess.run") as mock_run:
        notify("Title", "Body", enabled=False)

    mock_run.assert_not_called()


def test_notify_escapes_quotes():
    """notify escapes double quotes in title and body."""
    from phrasectl.macos import notify

    with patch("phrasectl.macos.subprocess.run") as mock_run:
        notify('Say "hello"', 'Body with "quotes"')

    mock_run.assert_called_once_with(
        ["osascript", "-e",
         'display notification "Body with \\"quotes\\"" with title "Say \\"hello\\""']
    )


def test_notify_escapes_backslashes_before_quotes():
    """notify escapes backslashes before quotes to prevent injection."""
    from phrasectl.macos import notify

    with patch("phrasectl.macos.subprocess.run") as mock_run:
        notify("Title", 'path\\to\\file')

    mock_run.assert_called_once_with(
        ["osascript", "-e",
         'display notification "path\\\\to\\\\file" with title "Title"']
    )
