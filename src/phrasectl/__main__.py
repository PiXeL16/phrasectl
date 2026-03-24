# ABOUTME: CLI entry point for phrasectl — handles argument parsing and orchestration.
# ABOUTME: Detects the current platform and delegates to the appropriate platform module.

from __future__ import annotations

import argparse
import os
import sys
import time
from types import ModuleType

from phrasectl.api import rephrase_text
from phrasectl.config import load_config, resolve_api_key, resolve_profile

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/phrasectl/config.toml")


def get_platform() -> ModuleType:
    """Return the platform-specific module for the current OS."""
    if sys.platform == "darwin":
        from phrasectl import macos
        return macos
    elif sys.platform == "linux":
        from phrasectl import linux
        return linux
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")


def main(argv: list[str] | None = None) -> None:
    """Main entry point for the phrasectl tool."""
    parser = argparse.ArgumentParser(description="AI text rephrasing tool")
    parser.add_argument("--profile", default=None, help="Rephrase profile to use")
    parser.add_argument("--list-profiles", action="store_true", help="List available profiles")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to config file")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    notifications_on = config.behavior.notifications

    # List profiles mode
    if args.list_profiles:
        for key, profile in config.profiles.items():
            default_marker = " (default)" if key == config.behavior.default_profile else ""
            print(f"  {key}: {profile.name}{default_marker}")
        return

    # Load platform-specific operations
    platform = get_platform()

    # Check for API key before doing anything else
    api_key = resolve_api_key(config)
    if not api_key:
        platform.notify(
            "phrasectl Error",
            "No API key found. Set ANTHROPIC_API_KEY or add key to config.",
            enabled=notifications_on,
        )
        return

    profile = resolve_profile(config, args.profile)

    # Detect if we're in a terminal for correct copy/paste shortcuts
    window_class = platform.get_active_window_class()
    is_terminal = platform.detect_terminal(window_class)

    # Save current clipboard for later restoration
    original_clipboard = platform.get_clipboard()

    # Copy the selected text
    platform.send_copy(is_terminal)
    time.sleep(platform.COPY_DELAY)

    # Read what was copied
    selected_text = platform.get_clipboard()

    # If nothing was selected, select all and try again
    if not selected_text or selected_text == original_clipboard:
        platform.send_select_all(is_terminal)
        time.sleep(platform.SELECT_ALL_DELAY)
        platform.send_copy(is_terminal)
        time.sleep(platform.COPY_DELAY)
        selected_text = platform.get_clipboard()

    # Check if anything was actually selected (even after select-all fallback)
    if not selected_text or selected_text == original_clipboard:
        platform.notify("phrasectl", "No text selected", enabled=notifications_on)
        return

    # Rephrase via API
    platform.notify("phrasectl", f"Rephrasing with '{profile.name}'...", enabled=notifications_on)

    try:
        result = rephrase_text(config, profile, selected_text)
    except Exception as e:
        platform.notify("phrasectl Error", str(e), enabled=notifications_on)
        if config.behavior.restore_clipboard:
            platform.set_clipboard(original_clipboard)
        return

    # Put result in clipboard and paste
    platform.set_clipboard(result)
    platform.send_paste(is_terminal)
    time.sleep(platform.PASTE_DELAY)

    # Restore original clipboard
    if config.behavior.restore_clipboard:
        time.sleep(platform.RESTORE_DELAY)
        platform.set_clipboard(original_clipboard)

    platform.notify("phrasectl", "Done!", enabled=notifications_on)


if __name__ == "__main__":
    main()
