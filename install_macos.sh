#!/bin/bash
# ABOUTME: macOS installer for phrasectl — checks prereqs, copies config, creates Quick Action.
# ABOUTME: Run once to set up the tool system-wide on macOS.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.config/phrasectl"
SERVICE_NAME="Rephrase with phrasectl"
WORKFLOW_DIR="$HOME/Library/Services/${SERVICE_NAME}.workflow"

echo "=== phrasectl Installer (macOS) ==="
echo ""

# Check prerequisites
MISSING=()
for cmd in uv osascript pbcopy pbpaste; do
    if ! command -v "$cmd" &>/dev/null; then
        MISSING+=("$cmd")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "Missing required tools: ${MISSING[*]}"
    echo ""
    if [[ " ${MISSING[*]} " == *" uv "* ]]; then
        echo "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
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

# Create Automator Quick Action (.workflow)
if [ -d "$WORKFLOW_DIR" ]; then
    echo "Quick Action already exists at $WORKFLOW_DIR (not overwriting)"
else
    echo "Creating Quick Action..."
    mkdir -p "$WORKFLOW_DIR/Contents"

    # Info.plist — minimal bundle metadata
    cat > "$WORKFLOW_DIR/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleName</key>
	<string>Rephrase with phrasectl</string>
	<key>CFBundleIdentifier</key>
	<string>com.phrasectl.quickaction</string>
	<key>NSServices</key>
	<array>
		<dict>
			<key>NSMenuItem</key>
			<dict>
				<key>default</key>
				<string>Rephrase with phrasectl</string>
			</dict>
			<key>NSMessage</key>
			<string>runWorkflowAsService</string>
			<key>NSPortName</key>
			<string>Rephrase with phrasectl</string>
		</dict>
	</array>
</dict>
</plist>
PLIST

    # document.wflow — Quick Action that runs a shell script with no input
    cat > "$WORKFLOW_DIR/Contents/document.wflow" << WFLOW
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>AMApplicationBuild</key>
	<string>523</string>
	<key>AMApplicationVersion</key>
	<string>2.10</string>
	<key>AMDocumentVersion</key>
	<string>2</string>
	<key>actions</key>
	<array>
		<dict>
			<key>action</key>
			<dict>
				<key>AMAccepts</key>
				<dict>
					<key>Container</key>
					<string>List</string>
					<key>Optional</key>
					<true/>
					<key>Types</key>
					<array>
						<string>com.apple.cocoa.string</string>
					</array>
				</dict>
				<key>AMActionVersion</key>
				<string>2.0.3</string>
				<key>AMApplication</key>
				<array>
					<string>Automator</string>
				</array>
				<key>AMParameterProperties</key>
				<dict>
					<key>COMMAND_STRING</key>
					<dict/>
					<key>CheckedForUserDefaultShell</key>
					<dict/>
					<key>inputMethod</key>
					<dict/>
					<key>shell</key>
					<dict/>
					<key>source</key>
					<dict/>
				</dict>
				<key>AMProvides</key>
				<dict>
					<key>Container</key>
					<string>List</string>
					<key>Types</key>
					<array>
						<string>com.apple.cocoa.string</string>
					</array>
				</dict>
				<key>ActionBundlePath</key>
				<string>/System/Library/Automator/Run Shell Script.action</string>
				<key>ActionName</key>
				<string>Run Shell Script</string>
				<key>ActionParameters</key>
				<dict>
					<key>COMMAND_STRING</key>
					<string>export PATH="\$HOME/.local/bin:\$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:\$PATH"
phrasectl</string>
					<key>CheckedForUserDefaultShell</key>
					<true/>
					<key>inputMethod</key>
					<integer>1</integer>
					<key>shell</key>
					<string>/bin/bash</string>
					<key>source</key>
					<string></string>
				</dict>
				<key>BundleIdentifier</key>
				<string>com.apple.RunShellScript</string>
				<key>CFBundleVersion</key>
				<string>2.0.3</string>
				<key>CanShowSelectedItemsWhenRun</key>
				<false/>
				<key>CanShowWhenRun</key>
				<true/>
				<key>Category</key>
				<array>
					<string>AMCategoryUtilities</string>
				</array>
				<key>Class Name</key>
				<string>RunShellScriptAction</string>
				<key>InputUUID</key>
				<string>A1B2C3D4-E5F6-7890-ABCD-EF1234567890</string>
				<key>Keywords</key>
				<array>
					<string>Shell</string>
					<string>Script</string>
					<string>Command</string>
					<string>Run</string>
					<string>Unix</string>
				</array>
				<key>OutputUUID</key>
				<string>B2C3D4E5-F6A7-8901-BCDE-F12345678901</string>
				<key>UUID</key>
				<string>C3D4E5F6-A7B8-9012-CDEF-123456789012</string>
				<key>UnlocalizedApplications</key>
				<array>
					<string>Automator</string>
				</array>
				<key>arguments</key>
				<dict>
					<key>0</key>
					<dict>
						<key>default value</key>
						<string>/bin/bash</string>
						<key>name</key>
						<string>shell</string>
						<key>required</key>
						<string>0</string>
						<key>type</key>
						<string>0</string>
					</dict>
					<key>1</key>
					<dict>
						<key>default value</key>
						<string></string>
						<key>name</key>
						<string>COMMAND_STRING</string>
						<key>required</key>
						<string>0</string>
						<key>type</key>
						<string>0</string>
					</dict>
					<key>2</key>
					<dict>
						<key>default value</key>
						<integer>1</integer>
						<key>name</key>
						<string>inputMethod</string>
						<key>required</key>
						<string>0</string>
						<key>type</key>
						<string>0</string>
					</dict>
					<key>3</key>
					<dict>
						<key>default value</key>
						<string></string>
						<key>name</key>
						<string>source</string>
						<key>required</key>
						<string>0</string>
						<key>type</key>
						<string>0</string>
					</dict>
				</dict>
				<key>isViewVisible</key>
				<integer>1</integer>
			</dict>
		</dict>
	</array>
	<key>connectors</key>
	<dict/>
	<key>workflowMetaData</key>
	<dict>
		<key>serviceInputTypeIdentifier</key>
		<string>com.apple.Automator.nothing</string>
		<key>serviceApplicationBundleID</key>
		<string>com.apple.finder</string>
		<key>workflowTypeIdentifier</key>
		<string>com.apple.Automator.servicesMenu</string>
	</dict>
</dict>
</plist>
WFLOW

    echo "Created Quick Action: $SERVICE_NAME"

    # Flush the services cache so macOS picks up the new Quick Action
    /System/Library/CoreServices/pbs -flush 2>/dev/null || true
    echo ""
    echo "To assign a keyboard shortcut:"
    echo "  1. Open System Settings > Keyboard > Keyboard Shortcuts > Services"
    echo "  2. Find 'Rephrase with phrasectl' under 'General'"
    echo "  3. Click 'Add Shortcut' and press your desired key combination"
    echo "     (e.g., Cmd+Shift+R)"
    echo ""
    echo "  Note: macOS requires Accessibility permissions for each app you use"
    echo "  the shortcut in. The first time you trigger it in a new app, macOS"
    echo "  will prompt you to grant access in System Settings > Privacy &"
    echo "  Security > Accessibility."
    echo ""
    echo "  If the service doesn't appear, try logging out and back in."
fi

# API key check
echo ""
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    if ! grep -q 'key = "sk-' "$CONFIG_DIR/config.toml" 2>/dev/null; then
        echo "No API key detected. Set it up with one of these methods:"
        echo ""
        echo "  Option 1 (recommended): Environment variable"
        echo "    Add to your ~/.zshrc or ~/.bash_profile:"
        echo "    export ANTHROPIC_API_KEY='your-key-here'"
        echo ""
        echo "  Option 2: Config file"
        echo "    Edit $CONFIG_DIR/config.toml and set [api] key = \"your-key-here\""
    fi
else
    echo "ANTHROPIC_API_KEY is set."
fi

echo ""
echo "=== Installation complete! ==="
echo "Assign a keyboard shortcut in System Settings to start rephrasing."
