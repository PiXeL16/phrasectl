#!/bin/bash
# ABOUTME: Linux/Wayland installer for phrasectl — checks prereqs, copies config, creates symlink, adds keybinding.
# ABOUTME: Run once to set up the tool system-wide on Linux with Hyprland.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.config/phrasectl"
BINDINGS_FILE="$HOME/.config/hypr/bindings.conf"

echo "=== phrasectl Installer (Linux) ==="
echo ""

# Check prerequisites
MISSING=()
for cmd in wl-copy wl-paste wtype hyprctl notify-send uv; do
    if ! command -v "$cmd" &>/dev/null; then
        MISSING+=("$cmd")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "Missing required tools: ${MISSING[*]}"
    echo "Please install them and re-run this script."
    exit 1
fi
echo "All prerequisites found."

# Create config directory and copy default config
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/config.toml" ]; then
    cp "$SCRIPT_DIR/config.toml" "$CONFIG_DIR/config.toml"
    chmod 700 "$CONFIG_DIR"
    echo "Created config at $CONFIG_DIR/config.toml"
else
    echo "Config already exists at $CONFIG_DIR/config.toml (not overwriting)"
fi

# Make wrapper executable and symlink
chmod +x "$SCRIPT_DIR/phrasectl"
mkdir -p "$HOME/.local/bin"
ln -sf "$SCRIPT_DIR/phrasectl" "$HOME/.local/bin/phrasectl"
echo "Symlinked phrasectl to ~/.local/bin/phrasectl"

# Pre-cache uv dependencies
echo "Pre-caching dependencies..."
uv run --project "$SCRIPT_DIR" python -m phrasectl --list-profiles
echo ""

# Add Hyprland keybinding
BINDING_LINE='bindd = SUPER SHIFT, R, phrasectl (fix), exec, phrasectl'
if [ -f "$BINDINGS_FILE" ]; then
    if ! grep -q "phrasectl" "$BINDINGS_FILE" 2>/dev/null; then
        echo "" >> "$BINDINGS_FILE"
        echo "# phrasectl — AI text rephrasing" >> "$BINDINGS_FILE"
        echo "$BINDING_LINE" >> "$BINDINGS_FILE"
        hyprctl reload
        echo "Added keybinding SUPER+SHIFT+R to $BINDINGS_FILE"
    else
        echo "Keybinding already exists in $BINDINGS_FILE"
    fi
else
    echo "Warning: $BINDINGS_FILE not found. Add this keybinding manually:"
    echo "  $BINDING_LINE"
fi

# API key check
echo ""
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    if ! grep -q 'key = "sk-' "$CONFIG_DIR/config.toml" 2>/dev/null; then
        echo "No API key detected. Set it up with one of these methods:"
        echo ""
        echo "  Option 1 (recommended): Environment variable"
        echo "    echo 'ANTHROPIC_API_KEY=your-key-here' > ~/.config/environment.d/phrasectl.conf"
        echo "    Then log out and back in (or reboot) for it to take effect."
        echo ""
        echo "  Option 2: Config file"
        echo "    Edit $CONFIG_DIR/config.toml and set [api] key = \"your-key-here\""
    fi
else
    echo "ANTHROPIC_API_KEY is set."
fi

echo ""
echo "=== Installation complete! ==="
echo "Select text in any app and press SUPER+SHIFT+R to rephrase."
