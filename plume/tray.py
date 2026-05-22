from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw

if TYPE_CHECKING:
    import pystray as _pystray

_ICON_SIZE = 64
_COLOR = (74, 144, 226, 255)


def _make_icon() -> Image.Image:
    img = Image.new("RGBA", (_ICON_SIZE, _ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = 4
    draw.ellipse([pad, pad, _ICON_SIZE - pad, _ICON_SIZE - pad], fill=_COLOR)
    return img


class TrayIcon:
    def __init__(
        self,
        on_fix: Callable[[], None],
        on_toggle: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._on_fix = on_fix
        self._on_toggle = on_toggle
        self._on_quit = on_quit
        self._icon: _pystray.Icon | None = None

    def start(self) -> None:
        try:
            import pystray

            menu = pystray.Menu(
                pystray.MenuItem("Corriger la sélection", lambda _i, _it: self._on_fix()),
                pystray.MenuItem(
                    "Afficher / Masquer le widget", lambda _i, _it: self._on_toggle()
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quitter", lambda _i, _it: self._on_quit()),
            )
            self._icon = pystray.Icon("plume", _make_icon(), "Plume", menu)
            thread = threading.Thread(
                target=self._icon.run, daemon=True, name="plume-tray"
            )
            thread.start()
        except Exception:
            # Tray is optional — app works fine without it
            pass

    def stop(self) -> None:
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
