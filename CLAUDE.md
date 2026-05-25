# Plume — French/English Text Fixer & Translator

## What this is

A desktop tool for Linux and Windows that fixes and translates text in any application via a global hotkey and an always-on-top floating widget. Supports 4 modes: fix French, fix English, translate FR→EN, translate EN→FR. Built for a developer on a QWERTY keyboard writing professional French without accent characters.

**The contract is strict: fix only spelling/accents/punctuation/grammar; never change meaning, never add or remove information.**

## ⚠️ GUI branch note

The original plan specifies PyQt6. This machine runs Ubuntu 20.04 (glibc 2.31) which is below PyQt6's minimum (glibc 2.34). Phases 3–5 are therefore implemented with **tkinter + pystray** instead. This is a temporary deviation — when the machine is upgraded to Ubuntu 22.04/24.04, the GUI should be rewritten with PyQt6.

## Current state — Phase 5 complete

```
plume/
├── pyproject.toml
├── plume.spec          # PyInstaller spec for Windows exe
├── installer.iss       # Inno Setup script for PlumeSetup.exe
├── plume.ico           # App icon (multi-size: 16/24/32/48/64/128/256)
├── .github/
│   └── workflows/
│       └── build-windows.yml  # CI: builds + publishes installer on v* tags
├── plume/
│   ├── __init__.py
│   ├── __main__.py     # CLI: init / fix / run subcommands
│   ├── app.py          # PlumeApp — bootstrap, wires everything
│   ├── capture.py      # capture_selection() — simulates Ctrl+C, reads clipboard
│   ├── clipboard.py    # get_clipboard() / set_clipboard() via pyperclip
│   ├── config.py       # Config (Pydantic v2) + Mode enum + load_config / save_config
│   ├── fixer.py        # async fix_text(text, cfg, mode) -> str
│   ├── gui_entry.py    # PyInstaller entry point — calls PlumeApp().run() directly
│   ├── hotkey.py       # GlobalHotkeyListener (pynput)
│   ├── notifier.py     # notify() — notify-send on Linux, plyer on Windows
│   ├── prompts.py      # get_prompt(mode) — 4 system prompts
│   ├── replace.py      # replace_selection() — sets clipboard, simulates Ctrl+V
│   ├── settings.py     # SettingsDialog (tkinter Toplevel, opened via right-click menu)
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
| `~/.config/plume/config.toml` (Linux) / `%LOCALAPPDATA%\plume\plume\config.toml` (Windows) | `api_base_url`, `model`, `hotkey`, `mode`, `widget_position` |
| same dir / `.env` | `PLUME_API_KEY` only — never written to TOML |

Paths via `platformdirs.user_config_dir("plume")`. `CONFIG_DIR` in `config.py` is monkeypatchable in tests.

## The 4 modes (config.py — Mode enum)

| Mode value | Label | Color | Action |
|---|---|---|---|
| `fix_french` | FR | Indigo | Fix French spelling/accents/grammar |
| `fix_english` | EN | Blue | Fix English spelling/grammar |
| `translate_fr_en` | F›E | Amber | Translate French → English |
| `translate_en_fr` | E›F | Purple | Translate English → French |

Right-clicking the widget opens a popup menu to switch mode. The chosen mode is saved to `config.toml` and persisted across restarts.

## App flow (select → shortcut → done)

1. User selects text in any app
2. User presses `Ctrl+Alt+F`
3. pynput intercepts the hotkey globally
4. `capture.py` simulates Ctrl+C and reads the clipboard
5. `fixer.py` picks the prompt for the active mode and sends text to LLM
6. `replace.py` writes the result to clipboard and simulates Ctrl+V
7. `notifier.py` shows a mode-specific desktop notification

## Response parsing (fixer.py)

1. Strip whitespace
2. Strip surrounding quotes (`"..."`, `'...'`, `"..."`)
3. Strip preamble lines small models add (see `_strip_preamble()`)
4. Strip markdown formatting the model may inject (`**bold**`, `*italic*`, `__x__`, `_x_`)

## First-run wizard (wizard.py)

Triggered automatically when `config.toml` does not exist. Shows a 3-step tkinter `Toplevel`: Welcome → form (API URL, key, model) → Done. Calls `save_config()` on completion. If the user cancels, the app exits cleanly.

## Settings dialog (settings.py)

Opened from the right-click popup menu on the widget (or tray menu when available). Fields: API URL, API key, model, hotkey. On save: writes config to disk and updates live `PlumeApp` state. If the hotkey changed, `GlobalHotkeyListener` is stopped and restarted immediately. Height is auto-sized after build so it fits on all platforms.

## Widget interaction (widget.py)

- Left-click: trigger fix/translate using the active mode
- Right-click: open popup menu (4 modes + Paramètres + Fermer ✕ to quit)
- Drag: reposition the widget anywhere on screen
- Widget label and ring color reflect the active mode
- States: idle → busy (pulsing ring) → success (emerald, 1.5 s) → idle

## Platform-specific behaviour

### Linux
- Circle mask via X11 Shape Extension (`_apply_circle_mask_x11`)
- Notifications via `notify-send`
- Clipboard via `pyperclip` + `xclip`

### Windows
- Circle mask via `wm_attributes("-transparentcolor", BG)` (`_apply_circle_mask_windows`)
- `WS_EX_NOACTIVATE` set on widget HWND so clicking it never steals focus from the source app
- Notifications via `plyer` (Windows-only dep, platform marker in `pyproject.toml`); toast uses `plume.ico` resolved via `sys._MEIPASS`
- Clipboard via `pyperclip` (works natively)

## Windows installer

Triggered by pushing a `v*` tag. GitHub Actions (`build-windows.yml`) runs on `windows-latest`:
1. `uv sync` + `uv pip install pyinstaller`
2. `pyinstaller plume.spec` → `dist/plume/` (onedir, no console; `plume.ico` bundled and embedded in the exe)
3. Inno Setup `installer.iss` → `Output/PlumeSetup.exe` (uses `plume.ico` via `SetupIconFile`)
4. Published as a GitHub Release asset

The installer: no admin rights needed, installs to `%ProgramFiles%\Plume`, adds startup registry entry (`HKCU\...\Run`), includes uninstaller.

To release:
```bash
git tag v0.x.0
git push origin v0.x.0
```

## Running the app (dev)

```bash
source "$HOME/snap/code/237/.local/share/../bin/env"
uv run plume run        # starts widget + tray + hotkey listener
uv run plume fix        # clipboard mode
uv run plume fix "text" # positional
```

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
- Runtime errors shown as desktop notifications

## Known gotchas

- PyQt6 blocked by glibc 2.31 on Ubuntu 20.04 — see GUI branch note above
- tkinter must be available on Linux: `sudo apt-get install python3-tk`
- pystray tray icon on GNOME requires AppIndicator extension + PyGObject — tray is silently disabled if unavailable; settings accessible via right-click on widget instead
- xclip required on Linux: `sudo apt-get install xclip`
- pynput GlobalHotKeys runs in a thread — UI updates must go through `root.after()`
- `asyncio_mode = "auto"` in pytest — no `@pytest.mark.asyncio` needed
- Root `Tk` window is withdrawn at startup and shown only after FloatingWidget is fully configured — avoids the "tk" title bar flash
- Some LLM models inject markdown formatting into their output — `_strip_markdown()` in `fixer.py` removes it

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
**Phase 4b — 4 modes (fix FR/EN, translate FR↔EN).** ✅ Done.
**Phase 5 — Cross-platform support (Linux + Windows).** ✅ Done.

## Hard constraints

- OS target: Linux + Windows.
- GUI: tkinter for now; PyQt6 on Ubuntu 22.04+
- No telemetry, no cloud sync, no analytics.
