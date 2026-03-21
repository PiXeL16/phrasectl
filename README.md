# phrasectl

AI-powered text rephrasing for Linux/Wayland. Select text in any app, press a hotkey, get it fixed.

## How it works

1. Select text in any app (Slack, Discord, email, browser, terminal)
2. Press `Super+Shift+R`
3. phrasectl copies the text, sends it to Claude, and pastes the result back
4. If nothing is selected, it selects all text in the input field first

Works with any Wayland app. Detects terminals automatically for correct copy/paste shortcuts.

## Requirements

- Linux with [Hyprland](https://hyprland.org/) (Wayland)
- [uv](https://docs.astral.sh/uv/) (Python package runner)
- `wl-copy`, `wl-paste` (from `wl-clipboard`)
- `wtype` (Wayland key simulation)
- `notify-send`
- An [Anthropic API key](https://console.anthropic.com/)

On Arch Linux:

```bash
pacman -S wl-clipboard wtype libnotify
```

## Install

```bash
git clone https://github.com/PiXeL16/phrasectl.git
cd phrasectl
./install.sh
```

The installer will:
- Check all prerequisites
- Copy the default config to `~/.config/phrasectl/config.toml`
- Symlink `phrasectl` to `~/.local/bin/`
- Add a `Super+Shift+R` keybinding to Hyprland
- Pre-cache Python dependencies

### API Key

Set your Anthropic API key with one of these methods:

**Option 1: Environment variable (recommended)**

```bash
echo 'ANTHROPIC_API_KEY=your-key-here' > ~/.config/environment.d/phrasectl.conf
```

Then log out and back in for it to take effect.

**Option 2: Config file**

Edit `~/.config/phrasectl/config.toml`:

```toml
[api]
key = "your-key-here"
```

## Profiles

phrasectl ships with four built-in profiles:

| Profile | Description |
|---------|-------------|
| `fix` (default) | Fix spelling, grammar, and punctuation. Preserves your voice. |
| `formal` | Rewrite in a formal, professional tone. |
| `casual` | Rewrite in a casual, friendly tone. |
| `concise` | Make the text shorter while keeping its meaning. |

List profiles:

```bash
phrasectl --list-profiles
```

Use a specific profile:

```bash
phrasectl --profile formal
```

You can add custom profiles in `~/.config/phrasectl/config.toml`:

```toml
[profiles.pirate]
name = "Talk Like a Pirate"
system_prompt = """Rewrite this text as if a pirate wrote it.
Return ONLY the rewritten text with no explanation."""
```

## Configuration

Config lives at `~/.config/phrasectl/config.toml`:

```toml
[api]
key = ""                      # Falls back to ANTHROPIC_API_KEY env var
model = "claude-sonnet-4-6"  # Model for rephrasing
max_tokens = 4096

[behavior]
default_profile = "fix"       # Profile used when no --profile flag
notifications = true          # Desktop notifications
restore_clipboard = true      # Restore clipboard after pasting
```

## Development

```bash
# Run tests
uv run --extra dev pytest

# Run tests with verbose output
uv run --extra dev pytest -v

# Run a specific test file
uv run --extra dev pytest tests/test_config.py -v
```

## How it's built

- Single Python script (`phrasectl.py`) with [PEP 723](https://peps.python.org/pep-0723/) inline dependencies
- `uv run --script` handles the virtual environment and `anthropic` package automatically
- `wtype` for key simulation (Ctrl+C/V for GUI apps, Ctrl+Shift+C/V for terminals)
- `wl-copy`/`wl-paste` for clipboard access
- `hyprctl` for active window detection
- `notify-send` for desktop notifications

## License

MIT
