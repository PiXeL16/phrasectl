# ABOUTME: Linux/Wayland platform implementation for phrasectl.
# ABOUTME: Provides clipboard, keyboard, window detection, and notification ops via Wayland tools.

from __future__ import annotations

import json
import subprocess

# Timing delays (seconds) for keystroke-to-clipboard synchronization
MODIFIER_RELEASE_DELAY = 0.5
COPY_DELAY = 0.5
SENTINEL_DELAY = 0.1
SELECT_ALL_DELAY = 0.3
PASTE_DELAY = 0.3
RESTORE_DELAY = 0.5

# Sentinel value placed in clipboard before sending copy keystroke.
# If clipboard still contains this after copy, the copy didn't work.
COPY_SENTINEL = "__phrasectl_awaiting_copy__"

TERMINAL_CLASSES = {
    "com.mitchellh.ghostty",
    "kitty",
    "alacritty",
    "foot",
    "org.wezfurlong.wezterm",
}


# --- Clipboard ---


def get_clipboard() -> str:
    """Read the current clipboard contents via wl-paste."""
    result = subprocess.run(
        ["wl-paste", "--no-newline"], capture_output=True, text=True
    )
    return result.stdout


def set_clipboard(text: str) -> None:
    """Write text to the clipboard via wl-copy."""
    process = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
    process.communicate(input=text.encode())


# --- Keyboard ---


def send_copy(is_terminal: bool = False) -> None:
    """Send copy keystroke to the active window via wtype."""
    if is_terminal:
        subprocess.run(["wtype", "-M", "ctrl", "-M", "shift", "-k", "c", "-m", "shift", "-m", "ctrl"], check=True)
    else:
        subprocess.run(["wtype", "-M", "ctrl", "-k", "c", "-m", "ctrl"], check=True)


def send_paste(is_terminal: bool = False) -> None:
    """Send paste keystroke to the active window via wtype."""
    if is_terminal:
        subprocess.run(["wtype", "-M", "ctrl", "-M", "shift", "-k", "v", "-m", "shift", "-m", "ctrl"], check=True)
    else:
        subprocess.run(["wtype", "-M", "ctrl", "-k", "v", "-m", "ctrl"], check=True)


def send_select_all(is_terminal: bool = False) -> None:
    """Send select-all keystroke to the active window via wtype."""
    subprocess.run(["wtype", "-M", "ctrl", "-k", "a", "-m", "ctrl"], check=True)


# --- Window detection ---


def get_active_window_class() -> str:
    """Get the window class of the currently focused window via hyprctl."""
    result = subprocess.run(
        ["hyprctl", "activewindow", "-j"], capture_output=True, text=True
    )
    if not result.stdout:
        return ""
    try:
        data = json.loads(result.stdout)
        return data.get("class", "")
    except json.JSONDecodeError:
        return ""


def detect_terminal(window_class: str) -> bool:
    """Check if the given window class belongs to a known terminal emulator."""
    return window_class.lower() in {c.lower() for c in TERMINAL_CLASSES}


# --- Notifications ---


def notify(title: str, body: str, enabled: bool = True) -> None:
    """Show a desktop notification via notify-send."""
    if not enabled:
        return
    subprocess.run(
        ["notify-send", "--app-name=phrasectl", "--expire-time=3000", title, body]
    )
