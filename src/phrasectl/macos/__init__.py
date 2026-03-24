# ABOUTME: macOS platform implementation for phrasectl.
# ABOUTME: Provides clipboard, keyboard, window detection, and notification ops via pbcopy/osascript.

from __future__ import annotations

import subprocess

# Timing delays (seconds) for keystroke-to-clipboard synchronization.
# osascript has more overhead than wtype, so macOS needs longer delays.
COPY_DELAY = 0.5
SELECT_ALL_DELAY = 0.5
PASTE_DELAY = 0.5
RESTORE_DELAY = 0.7

TERMINAL_APPS = {
    "terminal",
    "iterm2",
    "ghostty",
    "kitty",
    "alacritty",
    "wezterm",
}


# --- Clipboard ---


def get_clipboard() -> str:
    """Read the current clipboard contents via pbpaste."""
    result = subprocess.run(
        ["pbpaste"], capture_output=True, text=True
    )
    return result.stdout


def set_clipboard(text: str) -> None:
    """Write text to the clipboard via pbcopy."""
    process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    process.communicate(input=text.encode())


# --- Keyboard ---


def _applescript_keystroke(key: str, using: str = "command down") -> None:
    """Send a keystroke via AppleScript System Events."""
    subprocess.run(
        ["osascript", "-e", f'tell application "System Events" to keystroke "{key}" using {using}'],
        check=True,
    )


def send_copy(is_terminal: bool = False) -> None:
    """Send copy keystroke (Cmd+C) via osascript. is_terminal is ignored on macOS."""
    _applescript_keystroke("c")


def send_paste(is_terminal: bool = False) -> None:
    """Send paste keystroke (Cmd+V) via osascript. is_terminal is ignored on macOS."""
    _applescript_keystroke("v")


def send_select_all(is_terminal: bool = False) -> None:
    """Send select-all keystroke (Cmd+A) via osascript. is_terminal is ignored on macOS."""
    _applescript_keystroke("a")


# --- Window detection ---


def get_active_window_class() -> str:
    """Get the name of the frontmost application via osascript."""
    result = subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to get name of first application process whose frontmost is true'],
        capture_output=True, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def detect_terminal(window_class: str) -> bool:
    """Check if the given app name belongs to a known terminal emulator."""
    return window_class.lower() in TERMINAL_APPS


# --- Notifications ---


def notify(title: str, body: str, enabled: bool = True) -> None:
    """Show a desktop notification via osascript."""
    if not enabled:
        return
    # Escape backslashes first, then double quotes for AppleScript string literals
    safe_title = title.replace('\\', '\\\\').replace('"', '\\"')
    safe_body = body.replace('\\', '\\\\').replace('"', '\\"')
    subprocess.run(
        ["osascript", "-e",
         f'display notification "{safe_body}" with title "{safe_title}"']
    )
