# ABOUTME: System-wide AI text rephrasing tool for Linux/Wayland.
# ABOUTME: Copies selected text, sends it to Claude for rephrasing, and pastes the result back.
# /// script
# requires-python = ">=3.11"
# dependencies = ["anthropic"]
# ///

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import anthropic


class ConfigError(Exception):
    """Raised when config file cannot be parsed."""


@dataclass
class ApiConfig:
    key: str = ""
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 4096


@dataclass
class BehaviorConfig:
    default_profile: str = "fix"
    notifications: bool = True
    restore_clipboard: bool = True


@dataclass
class Profile:
    name: str
    system_prompt: str


DEFAULT_PROFILES = {
    "fix": Profile(
        name="Fix Grammar & Spelling",
        system_prompt=(
            "You are a text editor. Fix spelling, grammar, and punctuation errors.\n"
            "Smooth out awkward phrasing only when it is clearly clunky, but do not rewrite.\n"
            "Preserve the writer's natural voice: direct, conversational, and to the point.\n"
            "Keep sentences short and punchy. Do not add filler, formality, or flowery language.\n"
            "Do not add or remove content. Do not change the meaning.\n"
            "Return ONLY the corrected text with no explanation or commentary."
        ),
    ),
    "formal": Profile(
        name="Make Formal",
        system_prompt=(
            "You are a text editor. Rewrite the text in a formal, professional tone.\n"
            "Fix any spelling or grammar errors. Preserve the original meaning.\n"
            "Return ONLY the rewritten text with no explanation or commentary."
        ),
    ),
    "casual": Profile(
        name="Make Casual",
        system_prompt=(
            "You are a text editor. Rewrite the text in a casual, friendly tone.\n"
            "Fix any spelling or grammar errors. Preserve the original meaning.\n"
            "Return ONLY the rewritten text with no explanation or commentary."
        ),
    ),
    "concise": Profile(
        name="Make Concise",
        system_prompt=(
            "You are a text editor. Make the text more concise while preserving its meaning.\n"
            "Fix any spelling or grammar errors. Remove redundancy and unnecessary words.\n"
            "Return ONLY the rewritten text with no explanation or commentary."
        ),
    ),
}


@dataclass
class Config:
    api: ApiConfig = field(default_factory=ApiConfig)
    behavior: BehaviorConfig = field(default_factory=BehaviorConfig)
    profiles: dict[str, Profile] = field(default_factory=lambda: dict(DEFAULT_PROFILES))


def load_config(config_path: str) -> Config:
    """Load configuration from a TOML file, falling back to defaults for missing values."""
    path = Path(config_path)
    if not path.exists():
        return Config()

    try:
        with open(path, "rb") as f:
            raw = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Failed to parse config at {config_path}: {e}") from e

    api_raw = raw.get("api", {})
    api = ApiConfig(
        key=api_raw.get("key", ""),
        model=api_raw.get("model", "claude-sonnet-4-6"),
        max_tokens=api_raw.get("max_tokens", 4096),
    )

    behavior_raw = raw.get("behavior", {})
    behavior = BehaviorConfig(
        default_profile=behavior_raw.get("default_profile", "fix"),
        notifications=behavior_raw.get("notifications", True),
        restore_clipboard=behavior_raw.get("restore_clipboard", True),
    )

    profiles_raw = raw.get("profiles", {})
    if profiles_raw:
        profiles = {}
        for key, val in profiles_raw.items():
            profiles[key] = Profile(
                name=val.get("name", key),
                system_prompt=val.get("system_prompt", ""),
            )
    else:
        profiles = dict(DEFAULT_PROFILES)

    return Config(api=api, behavior=behavior, profiles=profiles)


def resolve_api_key(config: Config) -> str | None:
    """Resolve API key from config, falling back to ANTHROPIC_API_KEY env var."""
    if config.api.key:
        return config.api.key
    env_key = os.environ.get("ANTHROPIC_API_KEY")
    return env_key if env_key else None


def resolve_profile(config: Config, profile_name: str | None) -> Profile:
    """Resolve a profile by name, or use the default profile."""
    name = profile_name or config.behavior.default_profile
    if name not in config.profiles:
        raise ValueError(f"Unknown profile: '{name}'. Available: {list(config.profiles.keys())}")
    return config.profiles[name]


# --- Prompt construction ---


def get_system_prompt(profile: Profile) -> str:
    """Extract the system prompt string from a profile."""
    return profile.system_prompt


def build_messages(text: str) -> list[dict[str, str]]:
    """Build the messages list for the Claude API from user text."""
    return [{"role": "user", "content": text}]


# --- Clipboard operations ---

TERMINAL_CLASSES = {
    "com.mitchellh.ghostty",
    "kitty",
    "alacritty",
    "foot",
    "org.wezfurlong.wezterm",
}


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
    """Get the window class of the currently focused window."""
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


# --- Notification ---


def notify(title: str, body: str, enabled: bool = True) -> None:
    """Show a desktop notification via notify-send."""
    if not enabled:
        return
    subprocess.run(
        ["notify-send", "--app-name=phrasectl", "--expire-time=3000", title, body]
    )


# --- API call ---


def rephrase_text(config: Config, profile: Profile, text: str) -> str:
    """Send text to the Claude API for rephrasing and return the result."""
    api_key = config.api.key or None
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=config.api.model,
        max_tokens=config.api.max_tokens,
        system=get_system_prompt(profile),
        messages=build_messages(text),
    )
    return message.content[0].text


# --- CLI + main orchestration ---

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/phrasectl/config.toml")


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

    # Check for API key before doing anything else
    api_key = resolve_api_key(config)
    if not api_key:
        notify(
            "phrasectl Error",
            "No API key found. Set ANTHROPIC_API_KEY or add key to config.",
            enabled=notifications_on,
        )
        return

    profile = resolve_profile(config, args.profile)

    # Detect if we're in a terminal for correct copy/paste shortcuts
    window_class = get_active_window_class()
    is_terminal = detect_terminal(window_class)

    # Save current clipboard for later restoration
    original_clipboard = get_clipboard()

    # Copy the selected text
    send_copy(is_terminal)
    time.sleep(0.3)

    # Read what was copied
    selected_text = get_clipboard()

    # If nothing was selected, select all and try again
    if not selected_text or selected_text == original_clipboard:
        send_select_all(is_terminal)
        time.sleep(0.2)
        send_copy(is_terminal)
        time.sleep(0.3)
        selected_text = get_clipboard()

    # Check if anything was actually selected (even after select-all fallback)
    if not selected_text or selected_text == original_clipboard:
        notify("phrasectl", "No text selected", enabled=notifications_on)
        return

    # Rephrase via API
    notify("phrasectl", f"Rephrasing with '{profile.name}'...", enabled=notifications_on)

    try:
        result = rephrase_text(config, profile, selected_text)
    except Exception as e:
        notify("phrasectl Error", str(e), enabled=notifications_on)
        if config.behavior.restore_clipboard:
            set_clipboard(original_clipboard)
        return

    # Put result in clipboard and paste
    set_clipboard(result)
    send_paste(is_terminal)
    time.sleep(0.3)

    # Restore original clipboard
    if config.behavior.restore_clipboard:
        time.sleep(0.5)
        set_clipboard(original_clipboard)

    notify("phrasectl", "Done!", enabled=notifications_on)


if __name__ == "__main__":
    main()
