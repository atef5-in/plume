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
                pystray.MenuItem(
                    "Afficher / Masquer le widget", lambda _i, _it: self._on_toggle()
                ),
                pystray.MenuItem("Paramètres", lambda _i, _it: self._on_settings()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quitter", lambda _i, _it: self._on_quit()),
            )
            self._icon = pystray.Icon("plume", _make_icon(), "Plume", menu)
            thread = threading.Thread(
                target=self._run_silently, daemon=True, name="plume-tray"
            )
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
