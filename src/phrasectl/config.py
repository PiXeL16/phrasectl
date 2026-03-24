# ABOUTME: Configuration loading, profile resolution, and API key management.
# ABOUTME: Parses TOML config files and provides sensible defaults for all settings.

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


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
