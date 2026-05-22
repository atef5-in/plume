from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from plume.config import Config, save_config

_BG = "#1e1e2e"
_FG = "#cdd6f4"
_ENTRY_BG = "#313244"
_BTN_PRIMARY_BG = "#6366f1"
_BTN_SECONDARY_BG = "#45475a"
_WIDTH = 480
_HEIGHT = 340


def _center(win: tk.Toplevel) -> None:
    win.update_idletasks()
    x = (win.winfo_screenwidth() - _WIDTH) // 2
    y = (win.winfo_screenheight() - _HEIGHT) // 2
    win.geometry(f"{_WIDTH}x{_HEIGHT}+{x}+{y}")


class FirstRunWizard:
    def __init__(self, root: tk.Tk) -> None:
        self._result: Config | None = None
        self._step = 0

        self._win = tk.Toplevel(root)
        self._win.title("Plume — Configuration initiale")
        self._win.geometry(f"{_WIDTH}x{_HEIGHT}")
        self._win.resizable(False, False)
        self._win.configure(bg=_BG)
        self._win.grab_set()
        self._win.protocol("WM_DELETE_WINDOW", self._on_cancel)
        _center(self._win)

        self._frame = tk.Frame(self._win, bg=_BG)
        self._frame.pack(fill="both", expand=True, padx=30, pady=20)

        self._show_step()

    # ── helpers ───────────────────────────────────────────────────────────────

    def _clear(self) -> None:
        for w in self._frame.winfo_children():
            w.destroy()

    def _lbl(self, parent: tk.Widget, text: str, size: int = 11, bold: bool = False) -> tk.Label:
        return tk.Label(
            parent, text=text, bg=_BG, fg=_FG,
            font=("Arial", size, "bold" if bold else "normal"),
            wraplength=_WIDTH - 60, justify="left",
        )

    def _entry(self, parent: tk.Widget, show: str = "") -> tk.Entry:
        return tk.Entry(
            parent, bg=_ENTRY_BG, fg=_FG, insertbackground=_FG,
            relief="flat", font=("Arial", 11), show=show,
        )

    def _btn(self, parent: tk.Widget, text: str, command: object,
             primary: bool = True) -> tk.Button:
        bg = _BTN_PRIMARY_BG if primary else _BTN_SECONDARY_BG
        return tk.Button(
            parent, text=text, command=command,  # type: ignore[arg-type]
            bg=bg, fg=_FG, relief="flat",
            font=("Arial", 11, "bold" if primary else "normal"),
            padx=14, pady=6, cursor="hand2",
        )

    # ── steps ─────────────────────────────────────────────────────────────────

    def _show_step(self) -> None:
        self._clear()
        [self._show_welcome, self._show_form, self._show_done][self._step]()

    def _show_welcome(self) -> None:
        self._lbl(self._frame, "Bienvenue dans Plume", size=18, bold=True).pack(
            anchor="w", pady=(10, 8)
        )
        self._lbl(
            self._frame,
            "Plume corrige automatiquement votre français dans n'importe quelle "
            "application via un raccourci clavier global.\n\n"
            "Nous allons configurer l'accès à l'IA en quelques secondes.",
        ).pack(anchor="w", pady=(0, 20))

        bar = tk.Frame(self._frame, bg=_BG)
        bar.pack(side="bottom", fill="x")
        self._btn(bar, "Quitter", self._on_cancel, primary=False).pack(side="left")
        self._btn(bar, "Commencer →", self._next).pack(side="right")

    def _show_form(self) -> None:
        self._lbl(self._frame, "Connexion à l'IA", size=16, bold=True).pack(
            anchor="w", pady=(0, 10)
        )

        fields = tk.Frame(self._frame, bg=_BG)
        fields.pack(fill="x")

        def row(label: str, default: str = "", show: str = "") -> tk.Entry:
            tk.Label(fields, text=label, bg=_BG, fg=_FG, font=("Arial", 10)).pack(
                anchor="w", pady=(5, 1)
            )
            e = self._entry(fields, show=show)
            e.insert(0, default)
            e.pack(fill="x", ipady=4)
            return e

        self._e_url = row("URL de base de l'API", default="http://148.230.93.60:4000")
        self._e_key = row("Clé API", show="•")
        self._e_model = row("Modèle", default="ministral-3:8b-cloud")

        bar = tk.Frame(self._frame, bg=_BG)
        bar.pack(side="bottom", fill="x", pady=(10, 0))
        self._btn(bar, "← Retour", self._prev, primary=False).pack(side="left")
        self._btn(bar, "Enregistrer →", self._save_form).pack(side="right")

    def _show_done(self) -> None:
        self._lbl(self._frame, "Tout est prêt !", size=18, bold=True).pack(
            anchor="w", pady=(30, 10)
        )
        self._lbl(
            self._frame,
            "Plume est configuré.\n\n"
            "Sélectionnez du texte dans n'importe quelle application et appuyez sur "
            "Ctrl + Alt + F pour le corriger automatiquement.",
        ).pack(anchor="w")

        bar = tk.Frame(self._frame, bg=_BG)
        bar.pack(side="bottom", fill="x")
        self._btn(bar, "Lancer Plume", self._finish).pack(side="right")

    # ── actions ───────────────────────────────────────────────────────────────

    def _next(self) -> None:
        self._step += 1
        self._show_step()

    def _prev(self) -> None:
        self._step -= 1
        self._show_step()

    def _save_form(self) -> None:
        url = self._e_url.get().strip()
        key = self._e_key.get().strip()
        model = self._e_model.get().strip()

        if not url or not key or not model:
            messagebox.showerror(
                "Champs manquants", "Tous les champs sont obligatoires.", parent=self._win
            )
            return

        try:
            cfg = Config(api_base_url=url, api_key=key, model=model)
            save_config(cfg)
            self._result = cfg
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc), parent=self._win)
            return

        self._step += 1
        self._show_step()

    def _finish(self) -> None:
        self._win.grab_release()
        self._win.destroy()

    def _on_cancel(self) -> None:
        self._result = None
        self._win.grab_release()
        self._win.destroy()

    def result(self) -> Config | None:
        return self._result


def run_wizard(root: tk.Tk) -> Config | None:
    """Show the first-run wizard. Returns Config on success, None if cancelled."""
    w = FirstRunWizard(root)
    root.wait_window(w._win)
    return w.result()
