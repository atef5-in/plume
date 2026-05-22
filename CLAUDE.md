# Plume — French Text Fixer

## What this is

A desktop tool for Ubuntu that fixes French spelling, accents, apostrophes, and grammar in any application via a global hotkey and an always-on-top floating widget. Built for a developer working on a QWERTY keyboard who writes professional French (emails, tickets, docs) without accent characters.

**The contract is strict: fix only spelling/accents/punctuation/grammar; never change meaning, never add or remove information.**

## ⚠️ GUI branch note

The original plan specifies PyQt6. This machine runs Ubuntu 20.04 (glibc 2.31) which is below PyQt6's minimum (glibc 2.34). Phases 3–4 are therefore implemented with **tkinter + pystray** instead. This is a temporary deviation — when the machine is upgraded to Ubuntu 22.04/24.04, the GUI should be rewritten with PyQt6. The CLI (Phases 1–2) is unaffected.

## Current state — Phase 4 complete

```
plume/
├── pyproject.toml
├── .env.example
├── README.md
├── plume/
│   ├── __init__.py
│   ├── __main__.py     # CLI: init / fix / run subcommands
│   ├── app.py          # PlumeApp — bootstrap, wires everything
│   ├── capture.py      # capture_selection() — simulates Ctrl+C, reads clipboard
│   ├── clipboard.py    # get_clipboard() / set_clipboard() via pyperclip
│   ├── config.py       # Config (Pydantic v2) + load_config / save_config
│   ├── fixer.py        # async fix_text(text, cfg) -> str
│   ├── hotkey.py       # GlobalHotkeyListener (pynput)
│   ├── notifier.py     # notify() via notify-send
│   ├── prompts.py      # SYSTEM_PROMPT constant
│   ├── replace.py      # replace_selection() — sets clipboard, simulates Ctrl+V
│   ├── settings.py     # SettingsDialog (tkinter Toplevel, opened via right-click)
│   ├── tray.py         # TrayIcon (pystray, optional — fails gracefully on GNOME)
│   ├── widget.py       # FloatingWidget (tkinter, frameless, always-on-top)
│   └── wizard.py       # FirstRunWizard (tkinter Toplevel, shown on first launch)
└── tests/
    ├── test_clipboard.py
    ├── test_config.py
    ├── test_fixer.py
    ├── test_notifier.py
    └── test_prompts.py
```

## LLM endpoint

- **Base URL**: `http://148.230.93.60:4000` (internal LiteLLM proxy, no VPN needed)
- **Default model**: `ministral-3:8b-cloud` (confirmed working)
- Large models (mistral 675B, deepseek 671B) require a subscription — avoid them
- `gemini-3-flash-preview` is proprietary — avoid it

## Config files (runtime, not in repo)

| File | Contents |
|---|---|
| `~/.config/plume/config.toml` | `api_base_url`, `model`, `hotkey`, `widget_position` |
| `~/.config/plume/.env` | `PLUME_API_KEY` only — never written to TOML |

Paths via `platformdirs.user_config_dir("plume")`. `CONFIG_DIR` in `config.py` is monkeypatchable in tests.

## App flow (select → shortcut → done)

1. User selects text in any app
2. User presses `Ctrl+Alt+F`
3. pynput intercepts the hotkey globally
4. `capture.py` simulates Ctrl+C and reads the clipboard
5. `fixer.py` sends text to LLM
6. `replace.py` writes fixed text to clipboard and simulates Ctrl+V
7. `notifier.py` shows a desktop notification

The GNOME custom shortcut from Phase 2 should be **removed** — pynput handles the hotkey directly inside the running app.

## First-run wizard (wizard.py)

Triggered automatically when `~/.config/plume/config.toml` does not exist. Shows a 3-step tkinter `Toplevel`: Welcome → form (API URL, key, model) → Done. Calls `save_config()` on completion. If the user cancels, the app exits cleanly. The root `Tk` window is withdrawn during the wizard and shown only after it completes.

## Settings dialog (settings.py)

Opened by **right-clicking the floating widget**. Also accessible from the tray menu (when tray is available). A tkinter `Toplevel` with fields for API URL, API key, model, and hotkey. On save: writes config to disk and updates the live `PlumeApp` state. If the hotkey changed, the `GlobalHotkeyListener` is stopped and restarted immediately — no app restart needed.

## Widget interaction (widget.py)

- **Left-click**: trigger fix
- **Right-click**: open settings dialog
- **Drag**: reposition the widget anywhere on screen
- States: idle (indigo) → busy (pulsing ring) → success (emerald, 1.5 s) → idle

## Running the app

```bash
source "$HOME/snap/code/237/.local/share/../bin/env"
uv run plume run        # starts widget + tray + hotkey listener
uv run plume fix        # Phase 2 clipboard mode (still works)
uv run plume fix "text" # Phase 1 positional (still works)
```

To start automatically on login: add `plume run` to GNOME Startup Applications.

## Response parsing (fixer.py)

1. Strip whitespace
2. Strip surrounding quotes (`"..."`, `'...'`, `"..."`)
3. Strip preamble lines small models add (see `_strip_preamble()`)

## Code style

- `from __future__ import annotations` everywhere
- Full type hints, `mypy --strict` clean (with `pydantic.mypy` plugin)
- `ruff` lint + format: line length 100, select `E,F,I,UP,B`
- `plume/prompts.py` has `E501` ignored
- No hardcoded `~/.config` strings — always use `platformdirs`
- Async only for the LLM call; tkinter UI updates via `root.after()` from threads

## Error handling

- `ConfigError` — missing config
- `FixerError` — LLM timeout / HTTP errors
- `ClipboardError` — xclip missing or clipboard empty
- Runtime errors shown as desktop notifications via notify-send

## Known gotchas

- PyQt6 blocked by glibc 2.31 on Ubuntu 20.04 — see GUI branch note above
- tkinter must be available: `sudo apt-get install python3-tk` if missing
- pystray tray icon on GNOME requires AppIndicator extension + PyGObject; PyGObject won't build on Python 3.14 / Ubuntu 20.04 — tray is silently disabled, settings are accessible via right-click on the widget instead
- Widget corners are clipped to a true circle via the X11 Shape Extension (python-xlib, already installed via pynput)
- xclip required: `sudo apt-get install xclip`
- pynput GlobalHotKeys runs in a thread — UI updates must go through `root.after()`
- `asyncio_mode = "auto"` in pytest — no `@pytest.mark.asyncio` needed
- Root `Tk` window is withdrawn at startup and shown only after FloatingWidget is fully configured — avoids the "tk" title bar flash

## Running the checks

```bash
source "$HOME/snap/code/237/.local/share/../bin/env"
uv run pytest -v
uv run ruff check plume tests
uv run ruff format --check plume tests
uv run mypy plume
```

## Phased delivery

**Phase 1 — CLI only.** ✅ Done.
**Phase 2 — Clipboard mode.** ✅ Done.
**Phase 3 — tkinter widget + tray + hotkey listener.** ✅ Done.
**Phase 4 — Settings dialog + first-run wizard.** ✅ Done.
**Phase 5 — Cross-platform support (Linux + Windows).** Planned.

## Hard constraints

- OS target: Ubuntu (Linux + Windows in Phase 5). X11 uses `pynput` + `pyperclip`.
- GUI: tkinter for now; PyQt6 on Ubuntu 22.04+
- No telemetry, no cloud sync, no analytics.
- Logs: `~/.cache/plume/plume.log`, `RotatingFileHandler` 5 MB cap.
