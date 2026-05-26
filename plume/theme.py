from __future__ import annotations

import sys
import tkinter.font as tkfont

from plume.config import Mode

# ── color tokens (dark, default) ─────────────────────────────────────────────

APP_BG = "#0B0D12"
SURFACE = "#11141B"
SURFACE_ELEVATED = "#181C25"
SURFACE_HOVER = "#202636"
BORDER = "#2A3142"
BORDER_STRONG = "#3A4358"
TEXT_PRIMARY = "#F4F7FB"
TEXT_SECONDARY = "#A8B0C2"
TEXT_MUTED = "#747E94"
DANGER = "#F87171"
SUCCESS = "#34D399"
WARNING = "#FBBF24"

# Floating-widget transparent key color. Must equal the Tk root + canvas bg
# so the Windows -transparentcolor trick and the X11 shape mask agree on
# what is "outside" the circle.
WIDGET_BG_KEY = "#0d0d0d"

# Deep tinted fills for success/error states (kept close to surface so the
# ring carries the meaning, not a loud background).
SUCCESS_FILL = "#0F2A22"
ERROR_FILL = "#3A1414"

# ── mode accents (ring, deep fill) ───────────────────────────────────────────

MODE_ACCENTS: dict[Mode, tuple[str, str]] = {
    Mode.FIX_FRENCH: ("#7C83FF", "#252A63"),
    Mode.FIX_ENGLISH: ("#4C9DFF", "#173B68"),
    Mode.TRANSLATE_FR_EN: ("#F5A524", "#4A3415"),
    Mode.TRANSLATE_EN_FR: ("#B07CFF", "#352052"),
    Mode.REWRITE_TONE: ("#2DD4BF", "#123F3B"),
}

MODE_LABELS: dict[Mode, str] = {
    Mode.FIX_FRENCH: "FR",
    Mode.FIX_ENGLISH: "EN",
    Mode.TRANSLATE_FR_EN: "F›E",
    Mode.TRANSLATE_EN_FR: "E›F",
    Mode.REWRITE_TONE: "T",
}

# ── typography ───────────────────────────────────────────────────────────────

_WINDOWS_STACK = ("Segoe UI Variable", "Segoe UI", "Arial", "Helvetica")
_LINUX_STACK = (
    "Ubuntu",
    "Inter",
    "Noto Sans",
    "Cantarell",
    "DejaVu Sans",
    "Liberation Sans",
    "Arial",
    "Helvetica",  # X11 alias; resolves through fontconfig even in sandboxed envs
)

_cached_family: str | None = None


def ui_family() -> str:
    """Pick the first installed modern UI font. Case-insensitive match so
    snap-sandboxed Tk (which lowercases legacy X11 family names) still
    finds a real font instead of falling back to the bitmap default."""
    global _cached_family
    if _cached_family is not None:
        return _cached_family
    try:
        raw = list(tkfont.families())
    except Exception:
        raw = []
    available_lower = {f.lower(): f for f in raw}
    stack = _WINDOWS_STACK if sys.platform == "win32" else _LINUX_STACK
    for fam in stack:
        match = available_lower.get(fam.lower())
        if match is not None:
            _cached_family = match
            return match
    _cached_family = "Segoe UI" if sys.platform == "win32" else "DejaVu Sans"
    return _cached_family


# ── dialog tokens ────────────────────────────────────────────────────────────

DIALOG_BG = SURFACE
ENTRY_BG = SURFACE_ELEVATED
ENTRY_BORDER = BORDER

BTN_PRIMARY_BG = "#7C83FF"
BTN_PRIMARY_HOVER = "#9097FF"
BTN_PRIMARY_FG = "#0B0D12"

BTN_SECONDARY_BG = SURFACE_HOVER
BTN_SECONDARY_HOVER = BORDER_STRONG
BTN_SECONDARY_FG = TEXT_PRIMARY

# Muted warning callout
CALLOUT_BG = "#1F1A10"
CALLOUT_BORDER = "#4A3A18"
CALLOUT_FG = "#E6C76E"

# Tones list
LIST_BG = SURFACE_ELEVATED
LIST_ROW_HOVER = SURFACE_HOVER
LIST_ROW_SELECTED = SURFACE_HOVER
LIST_ROW_ACTIVE = "#1A2A2E"  # subtle teal-tinted bg for the active tone
LIST_ACTIVE_DOT = "#2DD4BF"  # teal — same as REWRITE_TONE accent


# ── spacing / radius ─────────────────────────────────────────────────────────

SP_4, SP_8, SP_12, SP_16, SP_20, SP_24, SP_32 = 4, 8, 12, 16, 20, 24, 32
# CustomTkinter's antialiasing can leave visibly jagged/notched corners on
# Linux/X11. Square controls look cleaner than broken rounded corners.
R_PILL, R_PANEL, R_CONTROL, R_CHIP = 999, 0, 0, 0


# ── helpers ──────────────────────────────────────────────────────────────────


def lighten(hex_color: str, amount: float) -> str:
    """Blend `hex_color` toward white by `amount` (0..1)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    return f"#{r:02x}{g:02x}{b:02x}"
