# Plume — French Text Fixer

## What this is

A desktop tool for Ubuntu that fixes French spelling, accents, apostrophes, and grammar in any application via a global hotkey and an always-on-top floating widget. Built for a developer working on a QWERTY keyboard who writes professional French (emails, tickets, docs) without accent characters.

**The contract is strict: fix only spelling/accents/punctuation/grammar; never change meaning, never add or remove information.**

## Current state — Phase 2 complete

CLI + clipboard mode working. GNOME shortcut configured. No GUI yet.

```
plume/
├── pyproject.toml
├── .env.example
├── README.md
├── plume/
│   ├── __init__.py
│   ├── __main__.py     # CLI: init / fix subcommands
│   ├── clipboard.py    # get_clipboard() / set_clipboard() via pyperclip
│   ├── config.py       # Config (Pydantic v2) + load_config / save_config
│   ├── fixer.py        # async fix_text(text, cfg) -> str
│   └── prompts.py      # SYSTEM_PROMPT constant
└── tests/
    ├── test_clipboard.py
    ├── test_config.py
    ├── test_fixer.py
    └── test_prompts.py
```

## LLM endpoint

- **Base URL**: `http://148.230.93.60:4000` (internal LiteLLM proxy, no VPN needed)
- **Default model**: `ministral-3:8b-cloud` (confirmed working)
- Other available models on this proxy: see the LiteLLM UI at `/ui`
- Large models (mistral 675B, deepseek 671B) require a subscription on this proxy — avoid them
- `gemini-3-flash-preview` is proprietary — avoid it

## Config files (runtime, not in repo)

| File | Contents |
|---|---|
| `~/.config/plume/config.toml` | `api_base_url`, `model`, `hotkey`, `widget_position` |
| `~/.config/plume/.env` | `PLUME_API_KEY` only — never written to TOML |

Paths via `platformdirs.user_config_dir("plume")`. `CONFIG_DIR` in `config.py` is monkeypatchable in tests.

## GNOME shortcut (Phase 2)

Configured in Settings → Keyboard → Custom Shortcuts:
- **Command**: `bash -c '/home/atef/My\ projects/Plume/.venv/bin/plume fix'`
- **Shortcut**: `Ctrl+Alt+F`

Flow: select text → Ctrl+C → Ctrl+Alt+F → Ctrl+V. Phase 3 will eliminate the manual Ctrl+C and Ctrl+V.

## Response parsing (fixer.py)

Three cleanup steps applied to the model's raw output:
1. Strip leading/trailing whitespace
2. Strip surrounding quotes (`"..."`, `'...'`, `"..."`)
3. Strip preamble lines small models add (e.g. `"Voici le texte corrigé :"`)

See `_strip_preamble()` and `_strip_surrounding_quotes()` in `plume/fixer.py`.

## Code style

- `from __future__ import annotations` everywhere
- Full type hints, `mypy --strict` clean (with `pydantic.mypy` plugin)
- `ruff` lint + format: line length 100, select `E,F,I,UP,B`
- `plume/prompts.py` has `E501` ignored (long lines are API prompt content)
- No hardcoded `~/.config` strings — always use `platformdirs`
- Async only for the LLM call (`fix_text`); everything else is sync

## Error handling

- `ConfigError` — raised by `load_config()` when required fields are missing
- `FixerError` — raised by `fix_text()` for: timeout, connect error, HTTP 4xx/5xx
- `ClipboardError` — raised by `get/set_clipboard()` when xclip is missing or clipboard is empty
- Errors go to stderr with non-zero exit in the CLI

## Known gotchas

- PyQt6 requires glibc ≥ 2.34; this machine has 2.31 — it's in `[project.optional-dependencies] gui`. Will be resolved in Phase 3.
- `asyncio_mode = "auto"` is set in pytest config — no `@pytest.mark.asyncio` needed.
- xclip must be installed: `sudo apt-get install xclip`
- In X11, the clipboard is owned by a process — avoid piping through xclip in the shortcut command; use `plume fix` directly instead.

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
- `plume fix` (no args) reads clipboard, writes fixed text back
- GNOME shortcut bound to `Ctrl+Alt+F`

**Phase 3 — PyQt6 widget, tray, global hotkey listener.**
- Eliminates manual Ctrl+C / Ctrl+V — just select + press shortcut
- New files: `app.py`, `widget.py`, `tray.py`, `hotkey.py`, `capture.py`, `replace.py`, `notifier.py`

**Phase 4 — Settings dialog + first-run wizard.**

Stop after each phase and confirm before continuing.

## Hard constraints (unchanged)

- OS target: Ubuntu. X11 uses `pynput` + `pyperclip`. Wayland requires `ydotool`.
- UI framework (Phase 3+): PyQt6 only, no other GUI deps.
- No telemetry, no cloud sync, no analytics.
- Logs: `~/.cache/plume/plume.log`, `RotatingFileHandler` 5 MB cap.
- Errors must surface to the user (toast in Phase 3+, stderr in CLI phases).
