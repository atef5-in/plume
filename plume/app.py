from __future__ import annotations

import asyncio
import threading
import time
import tkinter as tk

from plume.capture import capture_selection
from plume.config import CONFIG_DIR, Config, ConfigError, Mode, load_config, save_config
from plume.fixer import FixerError, fix_text
from plume.hotkey import GlobalHotkeyListener
from plume.notifier import notify
from plume.replace import replace_selection
from plume.tray import TrayIcon
from plume.widget import FloatingWidget

HOTKEY_SETTLE = 0.12  # seconds — let hotkey keys release before Ctrl+C

_MODE_MENU_LABELS: dict[Mode, str] = {
    Mode.FIX_FRENCH:      "Corriger le français",
    Mode.FIX_ENGLISH:     "Corriger l'anglais",
    Mode.TRANSLATE_FR_EN: "Traduire FR → EN",
    Mode.TRANSLATE_EN_FR: "Traduire EN → FR",
}

_MODE_DONE_MESSAGES: dict[Mode, str] = {
    Mode.FIX_FRENCH:      "✓ Français corrigé",
    Mode.FIX_ENGLISH:     "✓ English fixed",
    Mode.TRANSLATE_FR_EN: "✓ Translated to English",
    Mode.TRANSLATE_EN_FR: "✓ Texte traduit en français",
}


class PlumeApp:
    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.withdraw()  # hide until fully configured

        if not (CONFIG_DIR / "config.toml").exists():
            cfg = self._run_wizard()
            if cfg is None:
                self._root.destroy()
                raise SystemExit(0)
            self._cfg = cfg
        else:
            try:
                self._cfg = load_config()
            except ConfigError as exc:
                notify("Plume — Erreur de configuration", str(exc), "critical")
                raise

        self._widget = FloatingWidget(
            self._root,
            on_click=self.trigger_fix,
            on_right_click=self._show_mode_menu,
        )
        self._widget.update_mode(self._cfg.mode)
        self._root.deiconify()

        self._tray = TrayIcon(
            on_fix=self.trigger_fix,
            on_toggle=self._toggle_widget,
            on_quit=self.quit,
            on_settings=self._open_settings,
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

    def _run_wizard(self) -> Config | None:
        from plume.wizard import run_wizard
        return run_wizard(self._root)

    def _open_settings(self) -> None:
        from plume.settings import SettingsDialog
        self._root.after(0, lambda: SettingsDialog(self._root, self._cfg, self._apply_settings))

    def _apply_settings(self, cfg: Config) -> None:
        old_hotkey = self._cfg.hotkey
        self._cfg = cfg
        self._widget.update_mode(cfg.mode)
        if cfg.hotkey != old_hotkey:
            self._hotkey.stop()
            self._hotkey = GlobalHotkeyListener(hotkey=cfg.hotkey, callback=self.trigger_fix)
            self._hotkey.start()

    def _show_mode_menu(self, x: int, y: int) -> None:
        menu = tk.Menu(self._root, tearoff=0)
        for mode, label in _MODE_MENU_LABELS.items():
            prefix = "✓ " if mode == self._cfg.mode else "   "
            menu.add_command(
                label=f"{prefix}{label}",
                command=lambda m=mode: self._set_mode(m),  # type: ignore[misc]
            )
        menu.add_separator()
        menu.add_command(label="Paramètres", command=self._open_settings)
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _set_mode(self, mode: Mode) -> None:
        self._cfg = self._cfg.model_copy(update={"mode": mode})
        save_config(self._cfg)
        self._root.after(0, lambda: self._widget.update_mode(mode))

    def trigger_fix(self) -> None:
        if self._busy:
            return
        self._busy = True
        thread = threading.Thread(target=self._do_fix, daemon=True, name="plume-fix")
        thread.start()

    def _do_fix(self) -> None:
        mode = self._cfg.mode
        try:
            self._root.after(0, self._widget.set_busy)

            time.sleep(HOTKEY_SETTLE)
            text = capture_selection()

            if not text.strip():
                notify("Plume", "Rien à corriger — sélectionnez du texte d'abord.")
                self._root.after(0, self._widget.set_idle)
                return

            result = asyncio.run(fix_text(text, self._cfg, mode))
            replace_selection(result)

            msg = _MODE_DONE_MESSAGES[mode]
            notify("Plume", f"{msg} ({len(result)} caractères)")
            self._root.after(0, self._widget.set_success)

        except FixerError as exc:
            notify("Plume — Erreur", str(exc), "critical")
            self._root.after(0, self._widget.set_idle)
        except Exception as exc:
            notify("Plume — Erreur inattendue", str(exc), "critical")
            self._root.after(0, self._widget.set_idle)
        finally:
            self._busy = False
