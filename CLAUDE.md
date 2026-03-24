# phrasectl

## Project Names
- **AI**: Turbo "The Wordsmith" McFixit
- **Human**: ChrisCross FlameThrow Jimenez

## Overview
Cross-platform AI text rephrasing tool (Linux/Wayland and macOS). Select text in any app, press a hotkey, and get it rephrased by Claude.

## Commands

### Run tests
```bash
uv run --extra dev pytest
```

### Run specific test file
```bash
uv run --extra dev pytest tests/test_config.py -v
```

### Run the tool
```bash
uv run python -m phrasectl --list-profiles
uv run python -m phrasectl --profile fix
```

### Install
```bash
# Linux (Hyprland/Wayland)
./install_linux.sh

# macOS
./install_macos.sh
```

## Project Structure
- `src/phrasectl/` — Python package
  - `config.py` — Config loading, profiles, API key resolution
  - `prompt.py` — Prompt construction for Claude API
  - `api.py` — Anthropic client and text rephrasing
  - `__main__.py` — CLI entry point and orchestration
  - `linux/` — Linux/Wayland platform ops (wl-copy, wtype, hyprctl, notify-send)
  - `macos/` — macOS platform ops (pbcopy, osascript)
- `tests/` — Test suite (test_config, test_prompt, test_api, test_main, test_linux, test_macos)

## Tech Stack
- Python 3.11+ (stdlib `tomllib` for config)
- `anthropic` SDK (managed via `uv` + `pyproject.toml`)
- Linux: `wl-copy`, `wl-paste`, `wtype`, `hyprctl`, `notify-send`
- macOS: `pbcopy`, `pbpaste`, `osascript`
- Testing: `pytest` + `pytest-mock`

## Key Conventions
- TDD: tests written before implementation
- All code files start with ABOUTME comments
- No mock mode in production code (test files use pytest-mock at I/O boundaries)
- Platform-specific code lives in `linux/` and `macos/` folders
- Copy/paste uses `wtype` on Linux (with terminal detection) and `osascript` on macOS
