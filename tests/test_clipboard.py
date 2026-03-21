# ABOUTME: Tests for clipboard operations (get, set, save/restore).
# ABOUTME: Validates wl-copy/wl-paste/wtype subprocess interactions at the I/O boundary.

import subprocess
from unittest.mock import patch, MagicMock


def test_get_clipboard_calls_wl_paste():
    """get_clipboard calls wl-paste --no-newline and returns its stdout."""
    from phrasectl import get_clipboard

    mock_result = MagicMock()
    mock_result.stdout = "hello world"
    mock_result.returncode = 0

    with patch("phrasectl.subprocess.run", return_value=mock_result) as mock_run:
        result = get_clipboard()

    mock_run.assert_called_once_with(
        ["wl-paste", "--no-newline"], capture_output=True, text=True
    )
    assert result == "hello world"


def test_get_clipboard_returns_empty_on_failure():
    """get_clipboard returns empty string when wl-paste fails."""
    from phrasectl import get_clipboard

    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_result.returncode = 1

    with patch("phrasectl.subprocess.run", return_value=mock_result):
        result = get_clipboard()

    assert result == ""


def test_set_clipboard_pipes_to_wl_copy():
    """set_clipboard pipes text to wl-copy via stdin."""
    from phrasectl import set_clipboard

    mock_proc = MagicMock()
    mock_proc.communicate = MagicMock()

    with patch("phrasectl.subprocess.Popen", return_value=mock_proc) as mock_popen:
        set_clipboard("rephrased text")

    mock_popen.assert_called_once_with(["wl-copy"], stdin=subprocess.PIPE)
    mock_proc.communicate.assert_called_once_with(input=b"rephrased text")


def test_send_copy_gui_app():
    """send_copy sends Ctrl+C via wtype for GUI apps."""
    from phrasectl import send_copy

    with patch("phrasectl.subprocess.run") as mock_run:
        send_copy(is_terminal=False)

    mock_run.assert_called_once_with(
        ["wtype", "-M", "ctrl", "-k", "c", "-m", "ctrl"],
        check=True,
    )


def test_send_copy_terminal():
    """send_copy sends Ctrl+Shift+C via wtype for terminal apps."""
    from phrasectl import send_copy

    with patch("phrasectl.subprocess.run") as mock_run:
        send_copy(is_terminal=True)

    mock_run.assert_called_once_with(
        ["wtype", "-M", "ctrl", "-M", "shift", "-k", "c", "-m", "shift", "-m", "ctrl"],
        check=True,
    )


def test_send_paste_gui_app():
    """send_paste sends Ctrl+V via wtype for GUI apps."""
    from phrasectl import send_paste

    with patch("phrasectl.subprocess.run") as mock_run:
        send_paste(is_terminal=False)

    mock_run.assert_called_once_with(
        ["wtype", "-M", "ctrl", "-k", "v", "-m", "ctrl"],
        check=True,
    )


def test_send_paste_terminal():
    """send_paste sends Ctrl+Shift+V via wtype for terminal apps."""
    from phrasectl import send_paste

    with patch("phrasectl.subprocess.run") as mock_run:
        send_paste(is_terminal=True)

    mock_run.assert_called_once_with(
        ["wtype", "-M", "ctrl", "-M", "shift", "-k", "v", "-m", "shift", "-m", "ctrl"],
        check=True,
    )


def test_send_select_all():
    """send_select_all sends Ctrl+A via wtype."""
    from phrasectl import send_select_all

    with patch("phrasectl.subprocess.run") as mock_run:
        send_select_all()

    mock_run.assert_called_once_with(
        ["wtype", "-M", "ctrl", "-k", "a", "-m", "ctrl"],
        check=True,
    )
