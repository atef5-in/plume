from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox

from plume.config import Config, save_config

_BG = "#1e1e2e"
_FG = "#cdd6f4"
_ENTRY_BG = "#313244"
_BTN_PRIMARY_BG = "#6366f1"
_BTN_SECONDARY_BG = "#45475a"
_WIDTH = 440


def _center(win: tk.Toplevel) -> None:
    win.update_idletasks()
    h = win.winfo_reqheight()
    x = (win.winfo_screenwidth() - _WIDTH) // 2
    y = (win.winfo_screenheight() - h) // 2
    win.geometry(f"{_WIDTH}x{h}+{x}+{y}")


class SettingsDialog:
    def __init__(
        self,
        root: tk.Tk,
        cfg: Config,
        on_save: Callable[[Config], None],
    ) -> None:
        self._cfg = cfg
        self._on_save = on_save

        self._win = tk.Toplevel(root)
        self._win.title("Plume — Paramètres")
        self._win.resizable(False, False)
        self._win.configure(bg=_BG)
        self._win.grab_set()

        self._build()
        _center(self._win)

    def _entry(self, parent: tk.Widget, show: str = "") -> tk.Entry:
        return tk.Entry(
            parent,
            bg=_ENTRY_BG,
            fg=_FG,
            insertbackground=_FG,
            relief="flat",
            font=("Arial", 11),
            show=show,
        )

    def _build(self) -> None:
        frame = tk.Frame(self._win, bg=_BG)
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(frame, text="Paramètres", bg=_BG, fg=_FG, font=("Arial", 16, "bold")).pack(
            anchor="w", pady=(0, 14)
        )

        def row(label: str, default: str = "", show: str = "") -> tk.Entry:
            tk.Label(frame, text=label, bg=_BG, fg=_FG, font=("Arial", 10)).pack(
                anchor="w", pady=(5, 1)
            )
            e = self._entry(frame, show=show)
            e.insert(0, default)
            e.pack(fill="x", ipady=4)
            return e

        self._e_url = row("URL de base de l'API", default=self._cfg.api_base_url)
        self._e_key = row("Clé API", default=self._cfg.api_key.get_secret_value(), show="•")
        self._e_model = row("Modèle", default=self._cfg.model)
        self._e_hotkey = row("Raccourci clavier", default=self._cfg.hotkey)

        bar = tk.Frame(frame, bg=_BG)
        bar.pack(side="bottom", fill="x", pady=(10, 0))
        tk.Button(
            bar,
            text="Annuler",
            command=self._win.destroy,
            bg=_BTN_SECONDARY_BG,
            fg=_FG,
            relief="flat",
            font=("Arial", 11),
            padx=12,
            pady=6,
        ).pack(side="left")
        tk.Button(
            bar,
            text="Enregistrer",
            command=self._save,
            bg=_BTN_PRIMARY_BG,
            fg=_FG,
            relief="flat",
            font=("Arial", 11, "bold"),
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side="right")

    def _save(self) -> None:
        url = self._e_url.get().strip()
        key = self._e_key.get().strip()
        model = self._e_model.get().strip()
        hotkey = self._e_hotkey.get().strip()

        if not url or not key or not model or not hotkey:
            messagebox.showerror(
                "Champs manquants", "Tous les champs sont obligatoires.", parent=self._win
            )
            return

        try:
            cfg = Config(
                api_base_url=url,
                api_key=key,
                model=model,
                hotkey=hotkey,
                widget_position=self._cfg.widget_position,
            )
            save_config(cfg)
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc), parent=self._win)
            return

        self._on_save(cfg)
        self._win.destroy()
