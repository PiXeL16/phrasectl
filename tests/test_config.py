# ABOUTME: Tests for configuration loading, profile resolution, and API key fallback.
# ABOUTME: Validates TOML parsing, default values, and error handling for config.

import os
from pathlib import Path
from unittest.mock import patch

import pytest


def test_load_config_from_file(tmp_path):
    """Loading a valid TOML config file returns a Config with correct values."""
    from phrasectl import load_config

    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[api]
key = "sk-test-123"
model = "claude-sonnet-4-6"
max_tokens = 2048

[behavior]
default_profile = "formal"
notifications = false
restore_clipboard = false

[profiles.fix]
name = "Fix It"
system_prompt = "Fix the text."
""")

    config = load_config(str(config_file))
    assert config.api.key == "sk-test-123"
    assert config.api.model == "claude-sonnet-4-6"
    assert config.api.max_tokens == 2048
    assert config.behavior.default_profile == "formal"
    assert config.behavior.notifications is False
    assert config.behavior.restore_clipboard is False
    assert "fix" in config.profiles
    assert config.profiles["fix"].name == "Fix It"
    assert config.profiles["fix"].system_prompt == "Fix the text."


def test_load_config_missing_file_uses_defaults():
    """When config file doesn't exist, returns Config with sensible defaults."""
    from phrasectl import load_config

    config = load_config("/nonexistent/path/config.toml")
    assert config.api.key == ""
    assert config.api.model == "claude-sonnet-4-6"
    assert config.api.max_tokens == 4096
    assert config.behavior.default_profile == "fix"
    assert config.behavior.notifications is True
    assert config.behavior.restore_clipboard is True
    assert "fix" in config.profiles


def test_api_key_falls_back_to_env_var(tmp_path):
    """When config has empty API key, resolve_api_key returns env var value."""
    from phrasectl import load_config, resolve_api_key

    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[api]
key = ""
model = "claude-sonnet-4-6"
max_tokens = 4096

[behavior]
default_profile = "fix"
notifications = true
restore_clipboard = true

[profiles.fix]
name = "Fix"
system_prompt = "Fix."
""")

    config = load_config(str(config_file))
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-env-456"}):
        assert resolve_api_key(config) == "sk-env-456"


def test_api_key_prefers_config_over_env(tmp_path):
    """Config file API key takes precedence over environment variable."""
    from phrasectl import load_config, resolve_api_key

    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[api]
key = "sk-config-789"
model = "claude-sonnet-4-6"
max_tokens = 4096

[behavior]
default_profile = "fix"
notifications = true
restore_clipboard = true

[profiles.fix]
name = "Fix"
system_prompt = "Fix."
""")

    config = load_config(str(config_file))
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-env-456"}):
        assert resolve_api_key(config) == "sk-config-789"


def test_api_key_returns_none_when_nowhere_set(tmp_path):
    """When no API key in config or env, resolve_api_key returns None."""
    from phrasectl import load_config, resolve_api_key

    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[api]
key = ""
model = "claude-sonnet-4-6"
max_tokens = 4096

[behavior]
default_profile = "fix"
notifications = true
restore_clipboard = true

[profiles.fix]
name = "Fix"
system_prompt = "Fix."
""")

    config = load_config(str(config_file))
    with patch.dict(os.environ, {}, clear=True):
        # Remove ANTHROPIC_API_KEY if it exists
        env = os.environ.copy()
        env.pop("ANTHROPIC_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            assert resolve_api_key(config) is None


def test_resolve_profile_by_name(tmp_path):
    """resolve_profile returns the named profile from config."""
    from phrasectl import load_config, resolve_profile

    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[api]
key = ""
model = "claude-sonnet-4-6"
max_tokens = 4096

[behavior]
default_profile = "fix"
notifications = true
restore_clipboard = true

[profiles.fix]
name = "Fix"
system_prompt = "Fix it."

[profiles.formal]
name = "Formal"
system_prompt = "Make formal."
""")

    config = load_config(str(config_file))
    profile = resolve_profile(config, "formal")
    assert profile.name == "Formal"
    assert profile.system_prompt == "Make formal."


def test_resolve_profile_uses_default_when_none(tmp_path):
    """resolve_profile with None uses the default_profile from config."""
    from phrasectl import load_config, resolve_profile

    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[api]
key = ""
model = "claude-sonnet-4-6"
max_tokens = 4096

[behavior]
default_profile = "fix"
notifications = true
restore_clipboard = true

[profiles.fix]
name = "Fix"
system_prompt = "Fix it."
""")

    config = load_config(str(config_file))
    profile = resolve_profile(config, None)
    assert profile.name == "Fix"


def test_resolve_profile_unknown_name_raises(tmp_path):
    """resolve_profile raises ValueError for an unknown profile name."""
    from phrasectl import load_config, resolve_profile

    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[api]
key = ""
model = "claude-sonnet-4-6"
max_tokens = 4096

[behavior]
default_profile = "fix"
notifications = true
restore_clipboard = true

[profiles.fix]
name = "Fix"
system_prompt = "Fix it."
""")

    config = load_config(str(config_file))
    with pytest.raises(ValueError, match="Unknown profile"):
        resolve_profile(config, "nonexistent")


def test_load_config_invalid_toml(tmp_path):
    """Invalid TOML raises a ConfigError with a helpful message."""
    from phrasectl import ConfigError, load_config

    config_file = tmp_path / "config.toml"
    config_file.write_text("this is not [valid toml = ")

    with pytest.raises(ConfigError, match="Failed to parse"):
        load_config(str(config_file))


def test_load_config_partial_sections_use_defaults(tmp_path):
    """Config with missing sections fills in defaults for those sections."""
    from phrasectl import load_config

    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[api]
key = "sk-partial"
""")

    config = load_config(str(config_file))
    assert config.api.key == "sk-partial"
    # Missing sections should use defaults
    assert config.api.model == "claude-sonnet-4-6"
    assert config.behavior.default_profile == "fix"
    assert config.behavior.notifications is True
    assert "fix" in config.profiles
