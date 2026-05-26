from __future__ import annotations

import tkinter as tk

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

from plume import theme, ui
from plume.config import DEFAULT_TONES, Config, save_config

_WIDTH = 580
_HEIGHT = 520
_PAD = theme.SP_24
_CARD_PAD = 20
_TOTAL_STEPS = 3

ctk.set_appearance_mode("dark")


def _render_success_icon(size: int = 80) -> ImageTk.PhotoImage:
    """Antialiased emerald-tinted success circle with a check mark."""
    scale = 4
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 4 * scale
    box = (margin, margin, s - margin, s - margin)
    draw.ellipse(box, fill=theme.SUCCESS_FILL, outline=theme.SUCCESS, width=int(2.5 * scale))
    cx, cy = s / 2, s / 2
    pts = [
        (cx - 0.22 * s, cy + 0.02 * s),
        (cx - 0.05 * s, cy + 0.18 * s),
        (cx + 0.24 * s, cy - 0.16 * s),
    ]
    draw.line(pts, fill=theme.SUCCESS, width=int(3 * scale), joint="curve")
    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(resized)


class FirstRunWizard:
    def __init__(self, root: tk.Tk) -> None:
        self._result: Config | None = None
        self._step = 0
        self._success_icon: ImageTk.PhotoImage | None = None

        # Persistent draft values so navigating Retour/Commencer doesn't wipe input.
        self._draft_url = "http://148.230.93.60:4000"
        self._draft_key = ""
        self._draft_model = "ministral-3:8b-cloud"

        self._win = ctk.CTkToplevel(root)
        self._win.title("Plume — Configuration initiale")
        self._win.resizable(False, False)
        self._win.configure(fg_color=theme.APP_BG)
        self._win.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self._build_shell()
        x = (self._win.winfo_screenwidth() - _WIDTH) // 2
        y = (self._win.winfo_screenheight() - _HEIGHT) // 2
        self._win.geometry(f"{_WIDTH}x{_HEIGHT}+{x}+{y}")
        self._show_step()
        # Make sure the WM actually shows the window and gives it focus.
        self._win.deiconify()
        self._win.lift()
        self._win.after(50, self._win.focus_force)

    # ── shell + titlebar ──────────────────────────────────────────────────────

    def _build_shell(self) -> None:
        shell = ctk.CTkFrame(self._win, fg_color=theme.DIALOG_BG, corner_radius=0)
        shell.pack(fill="both", expand=True)
        self._build_progress(shell)

        self._content = ctk.CTkFrame(shell, fg_color="transparent")
        self._content.pack(fill="both", expand=True, padx=_PAD, pady=(theme.SP_16, _PAD))

    def _build_progress(self, parent: ctk.CTkBaseClass) -> None:
        """Three-segment progress bar with equal column widths."""
        wrap = ctk.CTkFrame(parent, fg_color="transparent", height=20)
        wrap.pack(fill="x", padx=_PAD, pady=(theme.SP_16, 0))
        for i in range(_TOTAL_STEPS):
            wrap.grid_columnconfigure(i, weight=1, uniform="step")
        self._segments: list[ctk.CTkFrame] = []
        for i in range(_TOTAL_STEPS):
            seg = ctk.CTkFrame(wrap, fg_color=theme.BORDER_STRONG, height=4, corner_radius=2)
            padx = (0, 6) if i == 0 else (3, 6) if i < _TOTAL_STEPS - 1 else (3, 0)
            seg.grid(row=0, column=i, sticky="ew", padx=padx)
            self._segments.append(seg)

    # ── step rendering ────────────────────────────────────────────────────────

    def _update_progress(self) -> None:
        for i, seg in enumerate(self._segments):
            if i <= self._step:
                seg.configure(fg_color=theme.BTN_PRIMARY_BG)
            else:
                seg.configure(fg_color=theme.BORDER_STRONG)

    def _capture_form_draft(self) -> None:
        """Read current step-2 form values into draft state, if visible."""
        if hasattr(self, "_e_url") and self._e_url.winfo_exists():
            self._draft_url = self._e_url.get()
            self._draft_key = self._e_key.get()
            self._draft_model = self._e_model.get()

    def _clear_content(self) -> None:
        for w in self._content.winfo_children():
            w.destroy()

    def _show_step(self) -> None:
        self._update_progress()
        self._clear_content()
        [self._show_welcome, self._show_form, self._show_done][self._step]()

    def _heading(self, parent: ctk.CTkBaseClass, text: str) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            text_color=theme.TEXT_PRIMARY,
            font=ui.font(22, bold=True),
            anchor="w",
        ).pack(anchor="w", fill="x")

    def _show_welcome(self) -> None:
        card = ui.card(self._content)
        card.pack(fill="both", expand=True)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=_CARD_PAD, pady=_CARD_PAD)

        self._heading(inner, "Bienvenue dans Plume")
        ui.helper(
            inner,
            "Plume corrige et traduit du texte dans n'importe quelle application "
            "via un raccourci clavier global.",
            wraplength=_WIDTH - 2 * _PAD - 2 * _CARD_PAD,
        ).pack(anchor="w", fill="x", pady=(theme.SP_8, theme.SP_20))

        for i, line in enumerate(
            (
                "Connecter Plume à votre modèle d'IA",
                "Sélectionner du texte dans n'importe quelle application",
                "Appuyer sur Ctrl + Alt + F pour le corriger",
            )
        ):
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(anchor="w", fill="x", pady=(0, theme.SP_8))
            ctk.CTkLabel(
                row,
                text=f"{i + 1}.",
                text_color=theme.BTN_PRIMARY_BG,
                font=ui.font(12, bold=True),
                width=20,
                anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text=line,
                text_color=theme.TEXT_SECONDARY,
                font=ui.font(12),
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

        bar = ctk.CTkFrame(self._content, fg_color="transparent")
        bar.pack(side="bottom", fill="x", pady=(theme.SP_16, 0))
        ui.secondary_button(bar, "Quitter", self._on_cancel).pack(side="left")
        ui.primary_button(bar, "Commencer", self._next).pack(side="right")

    def _show_form(self) -> None:
        card = ui.card(self._content)
        card.pack(fill="both", expand=True)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=_CARD_PAD, pady=_CARD_PAD)

        self._heading(inner, "Connexion à l'IA")
        ui.helper(
            inner,
            "Adresse et clé du modèle utilisé pour les corrections et traductions.",
            wraplength=_WIDTH - 2 * _PAD - 2 * _CARD_PAD,
        ).pack(anchor="w", fill="x", pady=(theme.SP_8, theme.SP_16))

        self._e_url = self._field(inner, "URL de base de l'API", self._draft_url)
        self._e_key = self._field(inner, "Clé API", self._draft_key, show="*")
        self._e_model = self._field(inner, "Modèle", self._draft_model)
        # Force keyboard focus to follow clicks — CTkEntry inside a frameless
        # grab_set window doesn't always grab focus on click on Linux WMs.
        for e in (self._e_url, self._e_key, self._e_model):
            e.bind("<Button-1>", lambda _ev, w=e: w.focus_set())

        bar = ctk.CTkFrame(self._content, fg_color="transparent")
        bar.pack(side="bottom", fill="x", pady=(theme.SP_16, 0))
        ui.secondary_button(bar, "Retour", self._prev).pack(side="left")
        ui.primary_button(bar, "Enregistrer", self._save_form).pack(side="right")

        self._win.after(80, self._e_url.focus_set)

    def _show_done(self) -> None:
        card = ui.card(self._content)
        card.pack(fill="both", expand=True)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(expand=True)  # centered

        self._success_icon = _render_success_icon(80)
        ctk.CTkLabel(inner, text="", image=self._success_icon).pack(pady=(0, theme.SP_16))

        ctk.CTkLabel(
            inner,
            text="Tout est prêt !",
            text_color=theme.TEXT_PRIMARY,
            font=ui.font(22, bold=True),
        ).pack()
        ctk.CTkLabel(
            inner,
            text=(
                "Sélectionnez du texte dans n'importe quelle application\n"
                "et appuyez sur Ctrl + Alt + F pour le corriger."
            ),
            text_color=theme.TEXT_MUTED,
            font=ui.font(12),
            justify="center",
        ).pack(pady=(theme.SP_8, 0))

        bar = ctk.CTkFrame(self._content, fg_color="transparent")
        bar.pack(side="bottom", fill="x", pady=(theme.SP_16, 0))
        ui.primary_button(bar, "Lancer Plume", self._finish, width=160).pack(side="right")

    def _field(
        self, parent: ctk.CTkBaseClass, label: str, default: str = "", show: str = ""
    ) -> ctk.CTkEntry:
        ui.field_label(parent, label).pack(anchor="w", pady=(0, theme.SP_4), fill="x")
        e = ui.entry(parent, show=show)
        if default:
            e.insert(0, default)
        e.pack(fill="x", pady=(0, theme.SP_12))
        return e

    # ── actions ───────────────────────────────────────────────────────────────

    def _next(self) -> None:
        self._step += 1
        self._show_step()

    def _prev(self) -> None:
        self._capture_form_draft()
        self._step -= 1
        self._show_step()

    def _save_form(self) -> None:
        url = self._e_url.get().strip()
        key = self._e_key.get().strip()
        model = self._e_model.get().strip()

        # Persist before doing anything else.
        self._draft_url, self._draft_key, self._draft_model = url, key, model

        if not url or not key or not model:
            ui.safe_alert(self._win, "Champs manquants", "Tous les champs sont obligatoires.")
            return

        try:
            cfg = Config(
                api_base_url=url,
                api_key=key,
                model=model,
                tones=[t.model_copy() for t in DEFAULT_TONES],
            )
            save_config(cfg)
            self._result = cfg
        except Exception as exc:
            ui.safe_alert(self._win, "Erreur", str(exc))
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
