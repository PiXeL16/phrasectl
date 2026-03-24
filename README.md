# phrasectl

AI-powered text rephrasing for Linux/Wayland and macOS. Select text in any app, press a hotkey, get it fixed.

## How it works

1. Select text in any app (Slack, Discord, email, browser, terminal)
2. Press your hotkey (`Super+Shift+R` on Linux, customizable on macOS)
3. phrasectl copies the text, sends it to Claude, and pastes the result back
4. If nothing is selected, it selects all text in the input field first

Works with any Wayland app on Linux and any app on macOS. Detects terminals automatically for correct copy/paste shortcuts on Linux.

## Requirements

### Linux (Hyprland/Wayland)

- [Hyprland](https://hyprland.org/) (Wayland compositor)
- [uv](https://docs.astral.sh/uv/) (Python package runner)
- `wl-copy`, `wl-paste` (from `wl-clipboard`)
- `wtype` (Wayland key simulation)
- `notify-send`
- An [Anthropic API key](https://console.anthropic.com/)

On Arch Linux:

```bash
pacman -S wl-clipboard wtype libnotify
```

### macOS

- [uv](https://docs.astral.sh/uv/) (Python package runner)
- An [Anthropic API key](https://console.anthropic.com/)

All other tools (`pbcopy`, `pbpaste`, `osascript`) are built into macOS.

## Install

```bash
git clone https://github.com/PiXeL16/phrasectl.git
cd phrasectl

# Linux (Hyprland/Wayland)
./install_linux.sh

# macOS
./install_macos.sh
```

### Linux installer

- Checks all prerequisites
- Copies the default config to `~/.config/phrasectl/config.toml`
- Symlinks `phrasectl` to `~/.local/bin/`
- Adds a `Super+Shift+R` keybinding to Hyprland
- Pre-caches Python dependencies

### macOS installer

- Checks prerequisites
- Copies the default config to `~/.config/phrasectl/config.toml`
- Symlinks `phrasectl` to `~/.local/bin/`
- Creates an Automator Quick Action (assignable to any keyboard shortcut)
- Pre-caches Python dependencies

After installing on macOS, assign a keyboard shortcut:
1. System Settings > Keyboard > Keyboard Shortcuts > Services
2. Find "Rephrase with phrasectl" under General
3. Click "Add Shortcut" and press your desired key combination

Note: macOS requires Accessibility permissions for each app you use the shortcut in. The first time you trigger it in a new app, macOS will prompt you to grant access in System Settings > Privacy & Security > Accessibility.

### API Key

Set your Anthropic API key:

**Option 1: Environment variable (recommended)**

```bash
# Add to ~/.zshrc (macOS) or ~/.bashrc (Linux)
export ANTHROPIC_API_KEY='your-key-here'
```

On Linux you can also use systemd user environment:

```bash
echo 'ANTHROPIC_API_KEY=your-key-here' > ~/.config/environment.d/phrasectl.conf
```

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

- Python package (`src/phrasectl/`) with platform-specific modules
- `uv run` handles the virtual environment and `anthropic` package automatically
- **Linux**: `wtype` for key simulation, `wl-copy`/`wl-paste` for clipboard, `hyprctl` for window detection, `notify-send` for notifications
- **macOS**: `osascript` (AppleScript) for key simulation, window detection, and notifications; `pbcopy`/`pbpaste` for clipboard

## License

MIT
