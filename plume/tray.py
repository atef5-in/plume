from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont

from plume import theme

if TYPE_CHECKING:
    import pystray as _pystray

_ICON_SIZE = 64
_RENDER_SCALE = 4


def _hex_to_rgba(h: str, alpha: int = 255) -> tuple[int, int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def _load_glyph_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Find any installed bold/regular TTF; fall back to PIL's default bitmap."""
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _make_icon() -> Image.Image:
    """Branded tray icon: dark circle, indigo accent ring, white 'P' glyph.
    Rendered at 4× and downsampled with LANCZOS for crisp antialiased edges."""
    s = _ICON_SIZE * _RENDER_SCALE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = 4 * _RENDER_SCALE
    ring_w = 2 * _RENDER_SCALE
    box = (margin, margin, s - margin, s - margin)
    draw.ellipse(
        box,
        fill=_hex_to_rgba(theme.SURFACE),
        outline=_hex_to_rgba(theme.BTN_PRIMARY_BG),
        width=int(ring_w),
    )

    font = _load_glyph_font(int(s * 0.55))
    glyph = "P"
    bbox = draw.textbbox((0, 0), glyph, font=font)
    gw, gh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (s - gw) // 2 - bbox[0]
    y = (s - gh) // 2 - bbox[1] - int(s * 0.02)  # nudge up for visual centering
    draw.text((x, y), glyph, fill=_hex_to_rgba(theme.TEXT_PRIMARY), font=font)

    return img.resize((_ICON_SIZE, _ICON_SIZE), Image.Resampling.LANCZOS)


class TrayIcon:
    def __init__(
        self,
        on_fix: Callable[[], None],
        on_toggle: Callable[[], None],
        on_quit: Callable[[], None],
        on_settings: Callable[[], None],
    ) -> None:
        self._on_fix = on_fix
        self._on_toggle = on_toggle
        self._on_quit = on_quit
        self._on_settings = on_settings
        self._icon: _pystray.Icon | None = None

    def start(self) -> None:
        try:
            import pystray

            menu = pystray.Menu(
                pystray.MenuItem("Corriger la sélection", lambda _i, _it: self._on_fix()),
                pystray.MenuItem("Afficher / Masquer le widget", lambda _i, _it: self._on_toggle()),
                pystray.MenuItem("Paramètres", lambda _i, _it: self._on_settings()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quitter", lambda _i, _it: self._on_quit()),
            )
            self._icon = pystray.Icon("plume", _make_icon(), "Plume", menu)
            thread = threading.Thread(target=self._run_silently, daemon=True, name="plume-tray")
            thread.start()
        except Exception:
            # Tray is optional — app works fine without it
            pass

    def _run_silently(self) -> None:
        import os

        # pystray prints GNOME docking errors at the C/X11 level — suppress fd 2
        devnull = os.open(os.devnull, os.O_WRONLY)
        saved = os.dup(2)
        os.dup2(devnull, 2)
        try:
            if self._icon is not None:
                self._icon.run()
        except Exception:
            pass
        finally:
            os.dup2(saved, 2)
            os.close(saved)
            os.close(devnull)

    def stop(self) -> None:
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
