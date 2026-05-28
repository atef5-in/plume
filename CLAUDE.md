# Plume — French/English Text Fixer & Translator (Sigma Telecoms build)

## What this is

A desktop tool for Linux and Windows that fixes and translates text in any application via a global hotkey and an always-on-top floating widget. Supports 5 modes: fix French, fix English, translate FR→EN, translate EN→FR, and rewrite-in-custom-tone (user-defined tones). Built for a developer on a QWERTY keyboard writing professional French without accent characters.

**This is the `client/sigma` branch** — a Sigma Telecoms variant where the LLM endpoint, key, and model are locked at build time so the settings UI exposes only the hotkey and tones. See [Sigma build differences](#sigma-build-differences) below.

**The contract is strict: fix only spelling/accents/punctuation/grammar; never change meaning, never add or remove information.** The rewrite-tone mode inherits the same fidelity contract — light rephrasing for register/tone is allowed, but no restructuring, no added or dropped information, dates/numbers/durations preserved verbatim.

## GUI stack

`tkinter` for the floating widget (frameless, shape-masked circle, Pillow-rendered) + `customtkinter` for dialogs (settings, first-run wizard, tone editor). PyQt6 is blocked by glibc 2.31 on Ubuntu 20.04 — when the dev machine upgrades to 22.04+, a PyQt6 rewrite remains the long-term direction, but the current customtkinter stack is the supported one.

## File map

```
plume/
├── plume.spec           # PyInstaller spec (includes customtkinter data files)
├── installer.iss        # Inno Setup script — OutputBaseFilename={#OutputName}
├── plume.ico            # App icon (multi-size: 16/24/32/48/64/128/256)
├── .github/workflows/
│   ├── build-windows.yml        # master build, v* tags → PlumeSetup.exe
│   └── build-windows-sigma.yml  # Sigma build, sigma-v* tags → PlumeSetup-Sigma.exe
└── plume/
    ├── sigma_secrets.env        # gitignored; bundled into the frozen app
    ├── sigma_secrets.env.example # placeholder template (committed)
    ├── __main__.py      # CLI: init / fix / run subcommands
    ├── app.py           # PlumeApp — bootstrap, wires everything
    ├── capture.py       # capture_selection()
    ├── clipboard.py     # get/set via pyperclip
    ├── config.py        # Config (Pydantic v2) + Mode enum + Tone model
    ├── fixer.py         # async fix_text()
    ├── gui_entry.py     # PyInstaller entry point
    ├── hotkey.py        # GlobalHotkeyListener (pynput)
    ├── notifier.py      # notify-send (Linux) / plyer (Windows)
    ├── prompts.py       # get_prompt(mode) + get_rewrite_prompt(tone)
    ├── replace.py       # replace_selection()
    ├── theme.py         # color tokens, mode accents, font picker, spacing/radius scale
    ├── ui.py            # shared customtkinter widget builders (button/entry/card/safe_alert)
    ├── settings.py      # SettingsDialog + ToneEditor (CTkToplevel, OS chrome)
    ├── tray.py          # TrayIcon — branded Pillow icon, P glyph + indigo ring
    ├── widget.py        # FloatingWidget — Pillow-rendered idle/busy/success/error states
    └── wizard.py        # FirstRunWizard — 3-step CTkToplevel with progress bar
```

## LLM endpoint (Sigma build)

Endpoint URL, API key, and model are read from `plume/sigma_secrets.env` (gitignored) and **locked** — `load_config()` overrides whatever may sit in `config.toml` on every load. See `_load_sigma_secrets()` in `config.py`. In CI the file is written from `SIGMA_API_BASE_URL` / `SIGMA_API_KEY` / `SIGMA_MODEL` repo secrets before PyInstaller runs.

## Config files (runtime)

| File | Contents |
|---|---|
| `~/.config/plume/config.toml` (Linux) / `%LOCALAPPDATA%\plume\plume\config.toml` (Windows) | `hotkey`, `mode`, `widget_position`, `tones`, `active_tone` |

The Sigma build does **not** write a `.env` and does **not** persist `api_base_url`/`api_key`/`model` to disk. Paths via `platformdirs.user_config_dir("plume")`. `CONFIG_DIR` in `config.py` is monkeypatchable in tests; `_load_sigma_secrets` is monkeypatched in `tests/test_config.py`.

## The 5 modes (config.py — Mode enum)

| Mode value | Label | Accent | Action |
|---|---|---|---|
| `fix_french` | FR | Indigo `#7C83FF` | Fix French spelling/accents/grammar |
| `fix_english` | EN | Blue `#4C9DFF` | Fix English spelling/grammar |
| `translate_fr_en` | F›E | Amber `#F5A524` | Translate French → English |
| `translate_en_fr` | E›F | Purple `#B07CFF` | Translate English → French |
| `rewrite_tone` | T | Teal `#2DD4BF` | Rewrite in a user-defined French tone |

All accents and tokens live in `theme.py`. Right-click the widget to switch mode; selection is persisted to `config.toml`.

### Rewrite-tone mode (`config.Tone`, `prompts.get_rewrite_prompt`)

Users define tones (name + free-text description) in **Paramètres → Tons personnalisés**. Fresh installs and upgraded installs without tones are seeded with 5 defaults (`config.DEFAULT_TONES`): *Plus formel, Plus court, Plus long, Plus direct, Amical* — seeded by the first-run wizard, and backfilled by `load_config()` for configs that predate seeding. The right-click cascade **Réécrire en…** sets `mode=REWRITE_TONE` and `active_tone=<name>`. Prompt template `_REWRITE_TONE_TEMPLATE` in `prompts.py` enforces dates/numbers verbatim (Rule 5), no vague→precise (Rule 5bis), preserves tu/vous register (Rule 8). If `active_tone` is missing/unknown, `fixer._system_prompt()` raises `FixerError`. Deleting the active tone from settings falls back to `FIX_FRENCH`.

**Known limit**: transformative tones (commercial/marketing) tend to invent claims with small models. Settings shows an amber callout warning. Subtractive/register-shift tones (concis, diplomatique, formel) work well.

## App flow

1. User selects text
2. User presses `Ctrl+Alt+F`
3. pynput intercepts hotkey
4. `capture.py` simulates Ctrl+C, reads clipboard
5. `fixer.py` picks prompt for active mode, calls LLM
6. `replace.py` writes result and simulates Ctrl+V
7. `notifier.py` shows mode-specific notification

## Response parsing (fixer.py)

Strip whitespace → strip surrounding quotes → strip preamble lines → strip markdown formatting (`**bold**`, `*italic*`, `__x__`, `_x_`).

## UI architecture

**Floating widget** (`widget.py`): 52×52 frameless, Pillow-rendered at 4× and downsampled with LANCZOS. Idle = neutral fill + thin accent ring + bold label. Busy = bright rotating arc (900ms cycle). Success = emerald tint + check (1500ms hold). Error = red tint + `!` + 220ms shake (1500ms hold). PhotoImage held on instance so Tk doesn't GC it.

**Dialogs** (`settings.py`, `wizard.py`): customtkinter with `OS chrome`. We tried `overrideredirect(True)` + custom titlebar; it deadlocks keyboard input on Linux WMs. We dropped overrideredirect — OS titlebars look slightly different per platform but everything works. `grab_set()` is deferred 80ms via `after()` so the window is fully mapped first. All toplevels also call `deiconify() + lift() + focus_force()` on open — without this, Windows opens the dialog inactive (because the floating widget HWND has `WS_EX_NOACTIVATE`) and the first click on any button only activates the window instead of triggering the command.

**Shared UI module** (`ui.py`): `primary_button`, `secondary_button`, `card_action_button`, `entry`, `field_label`, `helper`, `section_header`, `card`, and `safe_alert(win, title, msg)` which releases grab around messagebox calls to prevent the frameless-modal deadlock.

**Settings dialog** (Sigma): 640×640, two cards. Compact **Raccourci** card (label-left/entry-right single row, no helper text) + **Tons personnalisés** card (260px list, scrolls past 5 tones, header with inline +Ajouter/Modifier/Supprimer, amber callout). The Connexion card from the upstream build is removed — the endpoint/key/model are not user-editable. Footer reserved with `side="bottom"` BEFORE packing cards so it can't get squeezed out.

**Wizard** (Sigma): 580×520, **2 steps** (Welcome → Done) with a 2-segment progress bar. Clicking "Commencer" calls `_load_sigma_secrets()`, builds a `Config` with the locked values + `DEFAULT_TONES`, saves it, and advances to Done. No form step, no draft state. Done step shows a Pillow-rendered emerald success circle.

**Tone editor**: 520×440 with the same patterns. Name field auto-focuses on open.

**Tray icon** (`tray.py`): branded Pillow icon — dark `SURFACE` circle, 2px indigo accent ring, white "P" glyph rendered with the first available bold TTF (DejaVu/Liberation/Ubuntu on Linux, Segoe UI/Arial on Windows), 4× render downsampled with LANCZOS.

## Widget interaction

- Left-click: trigger fix/translate/rewrite using active mode
- Right-click: popup menu (4 base modes + **Réécrire en…** cascade + Paramètres + Fermer ✕)
- Drag: reposition anywhere
- States: idle → busy → success/error → idle

## Platform-specific behaviour

**Linux**: circle mask via X11 Shape Extension. Notifications via `notify-send`. Clipboard via `pyperclip` + `xclip`. Tray needs `python3-gi` + AppIndicator extension to actually display; silently disabled otherwise (right-click on widget is the fallback).

**Windows**: circle mask via `wm_attributes("-transparentcolor", BG)`. `WS_EX_NOACTIVATE` on widget HWND so clicks never steal focus. Notifications via `plyer` (Windows-only dep, platform marker in `pyproject.toml`); toast uses `plume.ico` via `sys._MEIPASS`. Clipboard via `pyperclip` natively. Tray uses Win32 systray API — reliable.

## Windows installer

Two parallel workflows on `windows-latest`:

| Workflow | Trigger | Output |
|---|---|---|
| `.github/workflows/build-windows.yml` | `v*` tag | `PlumeSetup.exe` (master/upstream build) |
| `.github/workflows/build-windows-sigma.yml` | `sigma-v*` tag | `PlumeSetup-Sigma.exe` (this branch) |

Both run: `uv sync` → `uv pip install pyinstaller` → `pyinstaller plume.spec` → Inno Setup with `/DAppVersion=<version> /DOutputName=<name>` → GitHub Release asset.

**Sigma workflow extras** — first step writes `plume/sigma_secrets.env` from the `SIGMA_API_BASE_URL` / `SIGMA_API_KEY` / `SIGMA_MODEL` repo secrets (fails fast if `SIGMA_API_KEY` is empty). Without this file, PyInstaller would bundle nothing and the .exe would crash on launch.

`plume.spec` uses `collect_data_files("customtkinter")` to bundle theme JSON files and adds `plume/sigma_secrets.env` to `datas`. `installer.iss` parameterizes both `AppVersion` and `OutputName` via `#ifndef` guards.

To release: `git tag sigma-v0.x.0 && git push origin sigma-v0.x.0`.

## Running the app (dev)

```bash
source "$HOME/snap/code/237/.local/share/../bin/env"
uv run plume run        # widget + tray + hotkey listener
uv run plume fix        # clipboard mode
uv run plume fix "text" # positional
```

## Code style

- `from __future__ import annotations` everywhere
- Full type hints, `mypy --strict` clean (with `pydantic.mypy` plugin)
- `ruff` lint + format: line length 100, select `E,F,I,UP,B`
- `plume/prompts.py` ignores `E501`
- `customtkinter` has no type stubs — `mypy` override in `pyproject.toml`
- No hardcoded `~/.config` strings — always use `platformdirs`
- Async only for the LLM call; tkinter UI updates via `root.after()` from threads

## Error handling

- `ConfigError` — missing config
- `FixerError` — LLM timeout / HTTP errors / missing active tone
- `ClipboardError` — xclip missing or clipboard empty
- Runtime errors → desktop notification + widget red error state with shake

## Known gotchas

- **Snap-confined Tk** (e.g. VSCode snap terminal) only sees 30 legacy X11 bitmap fonts. `theme.ui_family()` is case-insensitive and falls back to `Helvetica` (X11 alias resolved via fontconfig). Production install is unaffected.
- **customtkinter `show=""` vs `show="•"`**: U+2022 misbehaves on some Tk builds — masked entries use `show="*"`.
- **CTkEntry click focus**: on Linux, clicking the wrapper doesn't always focus the inner tk.Entry. Both dialogs explicitly bind `<Button-1>` → `focus_set()` on each entry.
- **overrideredirect + grab_set deadlock**: combining the two on Linux WMs freezes keyboard input. We use OS chrome on all dialogs and defer `grab_set()` until after `wait_visibility()` / via `after(80, ...)`.
- **safe_alert grab juggling**: `messagebox.showerror` from inside a `grab_set` window can deadlock — `ui.safe_alert()` releases the grab around the messagebox and reacquires after.
- **PhotoImage GC**: Pillow images blitted onto a Canvas must be held on `self._tk_image` or Tk garbage-collects them and they disappear.
- **`pack_propagate(False)` on `CTkScrollableFrame`**: breaks the inner canvas geometry and child widgets never render. Only apply it to plain `CTkFrame` variants — the scrollable one manages its own size.
- **Right-click menu auto-dismiss**: `tk_popup` + a `finally: grab_release()` is the textbook pattern but the menu doesn't auto-close on Windows when the widget HWND has `WS_EX_NOACTIVATE`. Bind `<FocusOut>` → `menu.unpost()` and call `menu.focus_set()` after `tk_popup` (`app.py:_show_mode_menu`).
- **pystray on GNOME**: needs `python3-gi` + AppIndicator extension. Without them, pystray falls back to XEmbed which GNOME ignored years ago. Silently disabled — right-click widget menu is the fallback.
- **PyInstaller + customtkinter**: spec must include `collect_data_files("customtkinter")` and `darkdetect` as hidden import or the .exe fails at first dialog open.
- xclip required on Linux: `sudo apt-get install xclip`
- pynput GlobalHotKeys runs in a thread — UI updates must go through `root.after()`
- `asyncio_mode = "auto"` in pytest — no `@pytest.mark.asyncio` needed
- Root `Tk` window is withdrawn at startup, shown only after FloatingWidget is fully configured — avoids the "tk" title bar flash
- On Linux X11, override-redirect + shape-masked widgets leave "ghosts" if destroyed abruptly. `PlumeApp._shutdown()` withdraws + `update()`s 3× before `destroy()`
- Ctrl+C / Ctrl+Z from terminal: SIGINT → `quit()`, SIGTSTP → withdraw + raise SIGSTOP (Linux only). `_signal_pulse` runs a 200 ms heartbeat so signals run between mainloop iterations

## Running the checks

```bash
source "$HOME/snap/code/237/.local/share/../bin/env"
uv run pytest -v
uv run ruff check plume tests
uv run ruff format --check plume tests
uv run mypy plume
```

## Sigma build differences

Diff vs. master, in one place:

- **Locked LLM config**: `api_base_url` / `api_key` / `model` come from `plume/sigma_secrets.env` (gitignored, bundled by PyInstaller). `load_config()` ignores any value for these three fields in `config.toml` and overwrites them every load. `save_config()` does not persist them and does not write a `.env`.
- **Settings UI**: Connexion card removed. Only **Raccourci** (compact one-row) + **Tons personnalisés** remain. See `plume/settings.py`.
- **First-run wizard**: collapsed to 2 steps (Welcome → Done). "Commencer" auto-seeds the config; no API form. See `plume/wizard.py`.
- **CI**: separate `build-windows-sigma.yml`, triggered by `sigma-v*` tags, reads secrets from GH Actions secrets, emits `PlumeSetup-Sigma.exe`.
- **Tests**: `tests/test_config.py` monkeypatches `_load_sigma_secrets` to avoid coupling to the real bundled file.

Nothing else changes — the 5 modes, the floating widget, the tone editor, the response-parsing/fixer pipeline, and the fidelity contract are all identical to master.

## Hard constraints

- OS target: Linux + Windows
- GUI: tkinter + customtkinter (PyQt6 deferred until Ubuntu 22.04+)
- No telemetry, no cloud sync, no analytics
