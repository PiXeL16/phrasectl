# phrasectl

## Project Names
- **AI**: Turbo "The Wordsmith" McFixit
- **Human**: ChrisCross FlameThrow Jimenez

## Overview
System-wide AI text rephrasing tool for Linux (Hyprland/Wayland). Select text in any app, press a hotkey, and get it rephrased by Claude.

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
uv run --script phrasectl.py --list-profiles
uv run --script phrasectl.py --profile fix
```

### Install
```bash
./install.sh
```

## Tech Stack
- Python 3.11+ (stdlib `tomllib` for config)
- `anthropic` SDK (managed via PEP 723 inline deps + `uv`)
- Wayland tools: `wl-copy`, `wl-paste`, `wtype`, `hyprctl`, `notify-send`
- Testing: `pytest` + `pytest-mock`

## Key Conventions
- TDD: tests written before implementation
- All code files start with ABOUTME comments
- No mock mode in production code (test files use pytest-mock at I/O boundaries)
- Copy/paste uses `wtype` for key simulation with terminal detection (Ctrl+C vs Ctrl+Shift+C)
