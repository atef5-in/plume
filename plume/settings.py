from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox

from plume.config import Config, Mode, Tone, save_config

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
        self._tones: list[Tone] = [t.model_copy() for t in cfg.tones]

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

        tk.Label(frame, text="Tons personnalisés", bg=_BG, fg=_FG, font=("Arial", 10)).pack(
            anchor="w", pady=(12, 1)
        )
        tk.Label(
            frame,
            text=(
                "⚠ Les tons transformatifs (commercial, marketing) peuvent introduire\n"
                "    des inexactitudes. Relisez le texte avant de le coller."
            ),
            bg=_BG,
            fg="#f9a825",
            font=("Arial", 9),
            justify="left",
        ).pack(anchor="w", pady=(0, 4))
        self._tones_list = tk.Listbox(
            frame,
            bg=_ENTRY_BG,
            fg=_FG,
            selectbackground=_BTN_PRIMARY_BG,
            relief="flat",
            font=("Arial", 11),
            height=4,
            highlightthickness=0,
        )
        self._tones_list.pack(fill="x")
        self._refresh_tones_list()

        tones_bar = tk.Frame(frame, bg=_BG)
        tones_bar.pack(fill="x", pady=(4, 0))
        for label, cmd in (
            ("Ajouter", self._tone_add),
            ("Modifier", self._tone_edit),
            ("Supprimer", self._tone_delete),
        ):
            tk.Button(
                tones_bar,
                text=label,
                command=cmd,
                bg=_BTN_SECONDARY_BG,
                fg=_FG,
                relief="flat",
                font=("Arial", 10),
                padx=8,
                pady=3,
            ).pack(side="left", padx=(0, 6))

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

    def _refresh_tones_list(self) -> None:
        self._tones_list.delete(0, tk.END)
        for tone in self._tones:
            self._tones_list.insert(tk.END, tone.name)

    def _selected_tone_index(self) -> int | None:
        sel = self._tones_list.curselection()  # type: ignore[no-untyped-call]
        return int(sel[0]) if sel else None

    def _tone_add(self) -> None:
        ToneEditor(self._win, None, self._tones, self._on_tone_saved)

    def _tone_edit(self) -> None:
        idx = self._selected_tone_index()
        if idx is None:
            return
        ToneEditor(self._win, idx, self._tones, self._on_tone_saved)

    def _tone_delete(self) -> None:
        idx = self._selected_tone_index()
        if idx is None:
            return
        del self._tones[idx]
        self._refresh_tones_list()

    def _on_tone_saved(self) -> None:
        self._refresh_tones_list()

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

        tone_names = {t.name for t in self._tones}
        active_tone = self._cfg.active_tone if self._cfg.active_tone in tone_names else None
        mode = self._cfg.mode
        if mode == Mode.REWRITE_TONE and active_tone is None:
            mode = Mode.FIX_FRENCH

        try:
            cfg = Config(
                api_base_url=url,
                api_key=key,
                model=model,
                hotkey=hotkey,
                mode=mode,
                widget_position=self._cfg.widget_position,
                tones=self._tones,
                active_tone=active_tone,
            )
            save_config(cfg)
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc), parent=self._win)
            return

        self._on_save(cfg)
        self._win.destroy()


class ToneEditor:
    def __init__(
        self,
        parent: tk.Toplevel,
        index: int | None,
        tones: list[Tone],
        on_saved: Callable[[], None],
    ) -> None:
        self._tones = tones
        self._index = index
        self._on_saved = on_saved

        self._win = tk.Toplevel(parent)
        self._win.title("Plume — Ton" if index is None else "Plume — Modifier le ton")
        self._win.configure(bg=_BG)
        self._win.transient(parent)
        self._win.grab_set()

        frame = tk.Frame(self._win, bg=_BG)
        frame.pack(fill="both", expand=True, padx=24, pady=18)

        tk.Label(frame, text="Nom", bg=_BG, fg=_FG, font=("Arial", 10)).pack(
            anchor="w", pady=(0, 1)
        )
        self._e_name = tk.Entry(
            frame,
            bg=_ENTRY_BG,
            fg=_FG,
            insertbackground=_FG,
            relief="flat",
            font=("Arial", 11),
            width=40,
        )
        self._e_name.pack(fill="x", ipady=4)

        tk.Label(frame, text="Description", bg=_BG, fg=_FG, font=("Arial", 10)).pack(
            anchor="w", pady=(8, 1)
        )
        self._t_desc = tk.Text(
            frame,
            bg=_ENTRY_BG,
            fg=_FG,
            insertbackground=_FG,
            relief="flat",
            font=("Arial", 11),
            height=6,
            width=40,
            wrap="word",
        )
        self._t_desc.pack(fill="both", expand=True)

        if index is not None:
            tone = tones[index]
            self._e_name.insert(0, tone.name)
            self._t_desc.insert("1.0", tone.description)

        bar = tk.Frame(frame, bg=_BG)
        bar.pack(fill="x", pady=(10, 0))
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

        self._win.update_idletasks()
        w = self._win.winfo_reqwidth()
        h = self._win.winfo_reqheight()
        x = (self._win.winfo_screenwidth() - w) // 2
        y = (self._win.winfo_screenheight() - h) // 2
        self._win.geometry(f"{w}x{h}+{x}+{y}")

    def _save(self) -> None:
        name = self._e_name.get().strip()
        desc = self._t_desc.get("1.0", "end").strip()
        if not name or not desc:
            messagebox.showerror(
                "Champs manquants",
                "Le nom et la description sont obligatoires.",
                parent=self._win,
            )
            return
        for i, existing in enumerate(self._tones):
            if existing.name == name and i != self._index:
                messagebox.showerror(
                    "Nom en double",
                    f"Un ton nommé « {name} » existe déjà.",
                    parent=self._win,
                )
                return
        tone = Tone(name=name, description=desc)
        if self._index is None:
            self._tones.append(tone)
        else:
            self._tones[self._index] = tone
        self._on_saved()
        self._win.destroy()
