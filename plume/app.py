from __future__ import annotations

import asyncio
import threading
import time
import tkinter as tk

from plume.capture import capture_selection
from plume.config import ConfigError, load_config
from plume.fixer import FixerError, fix_text
from plume.hotkey import GlobalHotkeyListener
from plume.notifier import notify
from plume.replace import replace_selection
from plume.tray import TrayIcon
from plume.widget import FloatingWidget

HOTKEY_SETTLE = 0.12  # seconds — let hotkey keys release before Ctrl+C


class PlumeApp:
    def __init__(self) -> None:
        try:
            self._cfg = load_config()
        except ConfigError as exc:
            notify("Plume — Erreur de configuration", str(exc), "critical")
            raise

        self._root = tk.Tk()
        self._widget = FloatingWidget(self._root, on_click=self.trigger_fix)
        self._tray = TrayIcon(
            on_fix=self.trigger_fix,
            on_toggle=self._toggle_widget,
            on_quit=self.quit,
        )
        self._hotkey = GlobalHotkeyListener(
            hotkey=self._cfg.hotkey,
            callback=self.trigger_fix,
        )
        self._busy = False

    def run(self) -> None:
        self._tray.start()
        self._hotkey.start()
        self._root.mainloop()

    def quit(self) -> None:
        self._hotkey.stop()
        self._tray.stop()
        self._root.after(0, self._root.quit)

    def _toggle_widget(self) -> None:
        if self._root.state() == "withdrawn":
            self._root.after(0, self._root.deiconify)
        else:
            self._root.after(0, self._root.withdraw)

    def trigger_fix(self) -> None:
        if self._busy:
            return
        self._busy = True
        thread = threading.Thread(target=self._do_fix, daemon=True, name="plume-fix")
        thread.start()

    def _do_fix(self) -> None:
        try:
            self._root.after(0, self._widget.set_busy)

            time.sleep(HOTKEY_SETTLE)
            text = capture_selection()

            if not text.strip():
                notify("Plume", "Rien à corriger — sélectionnez du texte d'abord.")
                self._root.after(0, self._widget.set_idle)
                return

            result = asyncio.run(fix_text(text, self._cfg))
            replace_selection(result)

            notify("Plume", f"✓ Texte corrigé ({len(result)} caractères)")
            self._root.after(0, self._widget.set_success)

        except FixerError as exc:
            notify("Plume — Erreur", str(exc), "critical")
            self._root.after(0, self._widget.set_idle)
        except Exception as exc:
            notify("Plume — Erreur inattendue", str(exc), "critical")
            self._root.after(0, self._widget.set_idle)
        finally:
            self._busy = False
