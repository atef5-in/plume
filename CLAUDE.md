# Plume — French/English Text Fixer & Translator

## What this is

A desktop tool for Linux and Windows that fixes and translates text in any application via a global hotkey and an always-on-top floating widget. Supports 5 modes: fix French, fix English, translate FR→EN, translate EN→FR, and rewrite-in-custom-tone (user-defined tones). Built for a developer on a QWERTY keyboard writing professional French without accent characters.

**The contract is strict: fix only spelling/accents/punctuation/grammar; never change meaning, never add or remove information.** The rewrite-tone mode inherits the same fidelity contract — light rephrasing for register/tone is allowed, but no restructuring, no added or dropped information, dates/numbers/durations preserved verbatim.

## ⚠️ GUI branch note

The original plan specifies PyQt6. This machine runs Ubuntu 20.04 (glibc 2.31) which is below PyQt6's minimum (glibc 2.34). Phases 3–5 are therefore implemented with **tkinter + pystray** instead. This is a temporary deviation — when the machine is upgraded to Ubuntu 22.04/24.04, the GUI should be rewritten with PyQt6.

## Current state — Phase 6 complete

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
│   ├── config.py       # Config (Pydantic v2) + Mode enum + Tone model + load_config / save_config
│   ├── fixer.py        # async fix_text(text, cfg, mode) -> str  (resolves tone for REWRITE_TONE)
│   ├── gui_entry.py    # PyInstaller entry point — calls PlumeApp().run() directly
│   ├── hotkey.py       # GlobalHotkeyListener (pynput)
│   ├── notifier.py     # notify() — notify-send on Linux, plyer on Windows
│   ├── prompts.py      # get_prompt(mode) + get_rewrite_prompt(tone_description)
│   ├── replace.py      # replace_selection() — sets clipboard, simulates Ctrl+V
│   ├── settings.py     # SettingsDialog + ToneEditor (tkinter Toplevels)
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
| `~/.config/plume/config.toml` (Linux) / `%LOCALAPPDATA%\plume\plume\config.toml` (Windows) | `api_base_url`, `model`, `hotkey`, `mode`, `widget_position`, `tones`, `active_tone` |
| same dir / `.env` | `PLUME_API_KEY` only — never written to TOML |

Paths via `platformdirs.user_config_dir("plume")`. `CONFIG_DIR` in `config.py` is monkeypatchable in tests.

## The 5 modes (config.py — Mode enum)

| Mode value | Label | Color | Action |
|---|---|---|---|
| `fix_french` | FR | Indigo | Fix French spelling/accents/grammar |
| `fix_english` | EN | Blue | Fix English spelling/grammar |
| `translate_fr_en` | F›E | Amber | Translate French → English |
| `translate_en_fr` | E›F | Purple | Translate English → French |
| `rewrite_tone` | T~ | Teal | Rewrite in a user-defined French tone |

Right-clicking the widget opens a popup menu to switch mode. The chosen mode is saved to `config.toml` and persisted across restarts.

### Rewrite-tone mode (`config.Tone`, `prompts.get_rewrite_prompt`)

Users define their own tones (name + free-text description) in **Paramètres → Tons personnalisés**. The right-click menu has a **Réécrire en…** cascade listing them; selecting one sets `mode=REWRITE_TONE` and `active_tone=<name>`, both persisted.

The prompt template (`_REWRITE_TONE_TEMPLATE` in `prompts.py`) bakes in strict fidelity rules including:
- Rule 5: reproduce dates/numbers/durations verbatim (with concrete counter-example *"fin du mois prochain" ≠ "fin du mois"*).
- Rule 5bis: never turn a vague expression into a precise one (*"depuis pas mal de temps" ≠ "depuis plusieurs mois"*).
- Rule 8: preserve tu/vous register throughout.

If `active_tone` is missing or unknown when REWRITE_TONE fires, `fixer._system_prompt()` raises `FixerError`. If the user deletes the active tone from the settings dialog, `_save()` falls back to `FIX_FRENCH` so the widget remains usable.

**Known limit**: transformative tones (commercial/marketing) tend to invent claims with small models like `ministral-3:8b-cloud`. The settings dialog shows an amber warning next to the tones list. Subtractive/register-shift tones (concis, diplomatique, formel) work well.

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

Opened from the right-click popup menu on the widget (or tray menu when available). Fields: API URL, API key, model, hotkey, plus a **Tons personnalisés** section (Listbox + Ajouter/Modifier/Supprimer buttons; modal `ToneEditor` Toplevel with name + multi-line description, validates uniqueness). On save: writes config to disk and updates live `PlumeApp` state. If the hotkey changed, `GlobalHotkeyListener` is stopped and restarted immediately. If the active tone was removed, mode falls back to `FIX_FRENCH`. Height is auto-sized after build so it fits on all platforms.

## Widget interaction (widget.py)

- Left-click: trigger fix/translate/rewrite using the active mode
- Right-click: open popup menu (4 base modes + **Réécrire en…** cascade of user tones + Paramètres + Fermer ✕ to quit)
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
- On Linux X11, override-redirect + shape-masked widgets leave "ghosts" if destroyed abruptly. `PlumeApp._shutdown()` withdraws + `update()`s 3× before `destroy()` to force the compositor to repaint
- Ctrl+C / Ctrl+Z from the terminal are wired to clean shutdowns: SIGINT → `quit()`, SIGTSTP → withdraw + raise SIGSTOP (Linux only; SIGCONT re-shows the widget). Signal handlers only run between Tk mainloop iterations, so `_signal_pulse` schedules a 200 ms heartbeat to keep them responsive

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
**Phase 6 — 5th mode: rewrite-in-custom-tone (user-defined tones).** ✅ Done.

## Hard constraints

- OS target: Linux + Windows.
- GUI: tkinter for now; PyQt6 on Ubuntu 22.04+
- No telemetry, no cloud sync, no analytics.
