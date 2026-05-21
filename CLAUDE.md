# Plume — French Text Fixer

## What this is

A desktop tool for Ubuntu that fixes French spelling, accents, apostrophes, and grammar in any application via a global hotkey and an always-on-top floating widget. Built for a developer working on a QWERTY keyboard who writes professional French (emails, tickets, docs) without accent characters.

**The contract is strict: fix only spelling/accents/punctuation/grammar; never change meaning, never add or remove information.**

## Current state — Phase 1 complete

CLI is fully working and tested. Config is saved. No GUI exists yet.

```
plume/
├── pyproject.toml          # uv-managed, Python ≥ 3.11
├── .env.example
├── README.md
├── plume/
│   ├── __init__.py
│   ├── __main__.py         # CLI: init / fix subcommands
│   ├── config.py           # Config (Pydantic v2) + load_config / save_config
│   ├── fixer.py            # async fix_text(text, cfg) -> str
│   └── prompts.py          # SYSTEM_PROMPT constant (do not bury this)
└── tests/
    ├── test_config.py      # roundtrip, key isolation, missing fields
    ├── test_fixer.py       # happy path, quote stripping, 401/500/timeout
    └── test_prompts.py     # sanity checks on prompt keywords
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

Paths are computed via `platformdirs.user_config_dir("plume")`. The module-level `CONFIG_DIR` variable in `config.py` can be monkeypatched in tests.

## The system prompt

Lives in `plume/prompts.py` as `SYSTEM_PROMPT`. The user tunes it directly. Key invariants tested in `test_prompts.py`:
- Contains `"Ne change JAMAIS le sens"`
- Contains `"N'ajoute AUCUNE information"`
- No markdown fences

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
- `httpx.ConnectError` is caught separately (DNS failure, refused connection)
- Errors go to stderr with non-zero exit in the CLI

## Known gotchas

- PyQt6 requires glibc ≥ 2.34; this machine has 2.31 — it's in `[project.optional-dependencies] gui`, not in main deps. Will be resolved in Phase 3.
- `asyncio_mode = "auto"` is set in pytest config — no `@pytest.mark.asyncio` decorator needed.
- `pytest-httpx` mocks: use `httpx.ConnectTimeout` not `httpx.ReadTimeout` for timeout test (constructor compatibility).

## Running the checks

```bash
source "$HOME/snap/code/237/.local/share/../bin/env"  # activate uv if not in PATH
uv run pytest -v
uv run ruff check plume tests
uv run ruff format --check plume tests
uv run mypy plume
```

## Phased delivery — do not skip ahead

**Phase 1 — CLI only.** ✅ Done.
- `plume init` — interactive setup, writes config, runs test call
- `plume fix --stdin` / `plume fix "<text>"` — corrects and prints

**Phase 2 — Clipboard mode, still no GUI.**
- `plume fix` (no args) reads from clipboard, writes fixed text back
- User binds to a GNOME custom shortcut for full select → hotkey → paste flow
- New file: `plume/clipboard.py`

**Phase 3 — PyQt6 widget, tray, global hotkey listener.**
- New files: `app.py`, `widget.py`, `tray.py`, `hotkey.py`, `capture.py`, `replace.py`, `notifier.py`

**Phase 4 — Settings dialog + first-run wizard.**

Stop after each phase and confirm before continuing.

## Hard constraints (unchanged)

- OS target: Ubuntu. X11 uses `pynput` + `pyperclip`. Wayland requires `ydotool`.
- UI framework (Phase 3+): PyQt6 only, no other GUI deps.
- No telemetry, no cloud sync, no analytics.
- Logs: `~/.cache/plume/plume.log`, `RotatingFileHandler` 5 MB cap.
- Errors must surface to the user (toast in Phase 3+, stderr in CLI phases).
