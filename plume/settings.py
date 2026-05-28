from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from plume import theme
from plume.config import Config, Mode, Tone, save_config
from plume.ui import (
    card as _card,
)
from plume.ui import (
    card_action_button as _card_action_button,
)
from plume.ui import (
    entry as _entry,
)
from plume.ui import (
    field_label as _field_label,
)
from plume.ui import (
    font as _font,
)
from plume.ui import (
    helper as _helper_raw,
)
from plume.ui import (
    primary_button as _primary_button,
)
from plume.ui import (
    safe_alert as _safe_alert,
)
from plume.ui import (
    secondary_button as _secondary_button,
)

_WIDTH = 640
_HEIGHT = 640
_PAD = theme.SP_24
_CARD_PAD = 18
_TONES_LIST_H = 260
_TONES_SCROLL_THRESHOLD = 5

ctk.set_appearance_mode("dark")
ctk.set_widget_scaling(1.0)


def _helper(parent: ctk.CTkBaseClass, text: str) -> ctk.CTkLabel:
    return _helper_raw(parent, text)


def _center(win: ctk.CTkToplevel, width: int, height: int | None = None) -> None:
    win.update_idletasks()
    h = height if height is not None else win.winfo_reqheight()
    x = (win.winfo_screenwidth() - width) // 2
    y = (win.winfo_screenheight() - h) // 2
    win.geometry(f"{width}x{h}+{x}+{y}")


class SettingsDialog:
    def __init__(
        self,
        root: ctk.CTkBaseClass,
        cfg: Config,
        on_save: Callable[[Config], None],
    ) -> None:
        self._cfg = cfg
        self._on_save = on_save
        self._tones: list[Tone] = [t.model_copy() for t in cfg.tones]
        self._selected_tone_idx: int | None = None
        self._tone_row_frames: list[ctk.CTkBaseClass] = []
        self._tones_list_parent: ctk.CTkBaseClass | None = None
        self._tones_scrollable = False

        self._win = ctk.CTkToplevel(root)
        self._win.title("Plume — Paramètres")
        self._win.resizable(False, False)
        self._win.configure(fg_color=theme.DIALOG_BG)
        self._win.protocol("WM_DELETE_WINDOW", self._win.destroy)

        self._build()
        _center(self._win, _WIDTH, _HEIGHT)
        # On Windows the dialog opens without foreground activation (parent
        # widget HWND has WS_EX_NOACTIVATE), so the first click on any button
        # only activates the window. Force focus so clicks fire immediately.
        self._win.deiconify()
        self._win.lift()
        self._win.after(50, self._win.focus_force)
        self._win.after(80, self._win.grab_set)

    def _build(self) -> None:
        shell = ctk.CTkFrame(self._win, fg_color=theme.DIALOG_BG, corner_radius=0)
        shell.pack(fill="both", expand=True)

        frame = ctk.CTkFrame(shell, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=_PAD, pady=(theme.SP_20, _PAD))

        ctk.CTkLabel(
            frame,
            text="Paramètres",
            text_color=theme.TEXT_PRIMARY,
            font=_font(22, bold=True),
            anchor="w",
        ).pack(anchor="w", fill="x")
        _helper(
            frame,
            "Raccourci global et tons de réécriture.",
        ).pack(anchor="w", fill="x", pady=(theme.SP_4, theme.SP_20))

        # Reserve the bottom strip for the footer BEFORE packing cards, so
        # the footer can't get squeezed out when cards consume the height.
        bar = ctk.CTkFrame(frame, fg_color="transparent")
        bar.pack(side="bottom", fill="x", pady=(theme.SP_20, 0))
        _secondary_button(bar, "Annuler", self._win.destroy).pack(side="left")
        _primary_button(bar, "Enregistrer", self._save).pack(side="right")

        hk_card = _card(frame)
        hk_card.pack(fill="x")
        hk_inner = ctk.CTkFrame(hk_card, fg_color="transparent")
        hk_inner.pack(fill="x", padx=_CARD_PAD, pady=theme.SP_12)
        row = ctk.CTkFrame(hk_inner, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(
            row,
            text="Raccourci clavier",
            text_color=theme.TEXT_PRIMARY,
            font=_font(13, bold=True),
            anchor="w",
        ).pack(side="left")
        self._e_hotkey = _entry(row)
        self._e_hotkey.configure(width=220)
        self._e_hotkey.insert(0, self._cfg.hotkey)
        self._e_hotkey.pack(side="right")
        self._e_hotkey.bind("<Button-1>", lambda _ev: self._e_hotkey.focus_set())

        tones_card = _card(frame)
        tones_card.pack(fill="x", pady=(theme.SP_16, 0))
        tones_inner = ctk.CTkFrame(tones_card, fg_color="transparent")
        tones_inner.pack(fill="x", padx=_CARD_PAD, pady=_CARD_PAD)
        tones_head = ctk.CTkFrame(tones_inner, fg_color="transparent")
        tones_head.pack(fill="x", pady=(0, theme.SP_12))
        ctk.CTkLabel(
            tones_head,
            text="Tons personnalisés",
            text_color=theme.TEXT_PRIMARY,
            font=_font(14, bold=True),
            anchor="w",
        ).pack(side="left")
        actions = ctk.CTkFrame(tones_head, fg_color="transparent")
        actions.pack(side="right")
        _card_action_button(actions, "+ Ajouter", self._tone_add).pack(
            side="left", padx=(0, theme.SP_8)
        )
        _card_action_button(actions, "Modifier", self._tone_edit).pack(
            side="left", padx=(0, theme.SP_8)
        )
        _card_action_button(actions, "Supprimer", self._tone_delete).pack(side="left")
        self._build_tones_list(tones_inner)
        self._build_callout(tones_inner)

    def _field(
        self,
        parent: ctk.CTkBaseClass,
        label: str,
        default: str = "",
        show: str = "",
        grid_col: int | None = None,
    ) -> ctk.CTkEntry:
        holder = ctk.CTkFrame(parent, fg_color="transparent")
        if grid_col is None:
            holder.pack(fill="x", pady=(0, theme.SP_12))
        else:
            padx = (0, theme.SP_12) if grid_col == 0 else (theme.SP_12, 0)
            holder.grid(row=0, column=grid_col, sticky="ew", padx=padx)
        _field_label(holder, label).pack(anchor="w", pady=(0, theme.SP_4), fill="x")
        e = _entry(holder, show=show)
        if default:
            e.insert(0, default)
        e.pack(fill="x")
        return e

    def _build_tones_list(self, parent: ctk.CTkBaseClass) -> None:
        self._tones_list_parent = parent
        self._tones_scrollable = len(self._tones) > _TONES_SCROLL_THRESHOLD
        self._tones_container = self._make_tones_container(parent, self._tones_scrollable)
        self._tones_container.pack(fill="x")
        # pack_propagate(False) breaks CTkScrollableFrame's inner canvas
        # geometry — only lock the size on the plain Frame variant.
        if not self._tones_scrollable:
            self._tones_container.pack_propagate(False)
        self._refresh_tones_list()

    def _make_tones_container(self, parent: ctk.CTkBaseClass, scrollable: bool) -> ctk.CTkBaseClass:
        if scrollable:
            self._tones_container = ctk.CTkScrollableFrame(
                parent,
                fg_color=theme.LIST_BG,
                border_color=theme.BORDER,
                border_width=1,
                corner_radius=theme.R_CONTROL,
                height=_TONES_LIST_H,
                scrollbar_button_color=theme.BORDER_STRONG,
                scrollbar_button_hover_color=theme.TEXT_MUTED,
            )
            return self._tones_container
        self._tones_container = ctk.CTkFrame(
            parent,
            fg_color=theme.LIST_BG,
            border_color=theme.BORDER,
            border_width=1,
            corner_radius=theme.R_CONTROL,
            height=_TONES_LIST_H,
        )
        return self._tones_container

    def _refresh_tones_list(self) -> None:
        needs_scroll = len(self._tones) > _TONES_SCROLL_THRESHOLD
        if needs_scroll != self._tones_scrollable and self._tones_list_parent is not None:
            self._tones_container.destroy()
            self._tones_scrollable = needs_scroll
            self._tones_container = self._make_tones_container(
                self._tones_list_parent, needs_scroll
            )
            self._tones_container.pack(fill="x")
            if not needs_scroll:
                self._tones_container.pack_propagate(False)

        for row in self._tone_row_frames:
            row.destroy()
        self._tone_row_frames.clear()

        active = self._cfg.active_tone if self._cfg.mode == Mode.REWRITE_TONE else None

        if not self._tones:
            empty = ctk.CTkLabel(
                self._tones_container,
                text="Aucun ton pour l'instant",
                text_color=theme.TEXT_MUTED,
                font=_font(12),
            )
            empty.pack(expand=True)
            self._tone_row_frames.append(empty)
            return

        for idx, tone in enumerate(self._tones):
            self._tone_row_frames.append(self._build_tone_row(idx, tone, active))

    def _build_tone_row(self, idx: int, tone: Tone, active: str | None) -> ctk.CTkFrame:
        is_selected = idx == self._selected_tone_idx
        is_active = tone.name == active
        if is_selected:
            bg = theme.LIST_ROW_SELECTED
        elif is_active:
            bg = theme.LIST_ROW_ACTIVE
        else:
            bg = theme.LIST_BG

        row = ctk.CTkFrame(
            self._tones_container,
            fg_color=bg,
            corner_radius=theme.R_CHIP,
            height=38,
        )
        row.pack(fill="x", padx=theme.SP_8, pady=(theme.SP_8 if idx == 0 else 0, 0))
        row.pack_propagate(False)

        dot = ctk.CTkLabel(
            row,
            text="●" if is_active else "",
            text_color=theme.LIST_ACTIVE_DOT,
            font=_font(12, bold=True),
            width=18,
        )
        dot.pack(side="left", padx=(theme.SP_8, 0))

        name = ctk.CTkLabel(
            row,
            text=tone.name,
            text_color=theme.TEXT_PRIMARY,
            font=_font(12),
            anchor="w",
        )
        name.pack(side="left", padx=(theme.SP_4, 0), fill="x", expand=True)

        def enter(_e: object) -> None:
            if idx != self._selected_tone_idx:
                row.configure(fg_color=theme.LIST_ROW_HOVER)

        def leave(_e: object) -> None:
            if idx != self._selected_tone_idx:
                row.configure(fg_color=theme.LIST_ROW_ACTIVE if is_active else theme.LIST_BG)

        for w in (row, dot, name):
            w.bind("<Button-1>", lambda _e, i=idx: self._select_tone(i))
            w.bind("<Double-Button-1>", lambda _e: self._tone_edit())
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)

        return row

    def _select_tone(self, idx: int) -> None:
        self._selected_tone_idx = idx
        self._refresh_tones_list()

    def _build_callout(self, parent: ctk.CTkBaseClass) -> None:
        callout = ctk.CTkFrame(
            parent,
            fg_color=theme.CALLOUT_BG,
            border_color=theme.CALLOUT_BORDER,
            border_width=1,
            corner_radius=theme.R_CONTROL,
        )
        callout.pack(fill="x", pady=(theme.SP_12, 0))
        ctk.CTkLabel(
            callout,
            text=(
                "Les tons transformatifs (commercial, marketing) peuvent introduire "
                "des inexactitudes. Relisez le texte avant de le coller."
            ),
            text_color=theme.CALLOUT_FG,
            font=_font(11),
            # Inside dialog padding, card padding, and callout's own padx — keep
            # the text safely within the visible card area.
            wraplength=_WIDTH - 2 * _PAD - 2 * _CARD_PAD - 2 * theme.SP_12 - 8,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=theme.SP_12, pady=theme.SP_8, fill="x")

    # ── tones actions ─────────────────────────────────────────────────────────

    def _tone_add(self) -> None:
        ToneEditor(self._win, None, self._tones, self._on_tone_saved)

    def _tone_edit(self) -> None:
        if self._selected_tone_idx is None:
            return
        ToneEditor(self._win, self._selected_tone_idx, self._tones, self._on_tone_saved)

    def _tone_delete(self) -> None:
        if self._selected_tone_idx is None:
            return
        del self._tones[self._selected_tone_idx]
        self._selected_tone_idx = None
        self._refresh_tones_list()

    def _on_tone_saved(self) -> None:
        self._refresh_tones_list()

    # ── save ──────────────────────────────────────────────────────────────────

    def _save(self) -> None:
        hotkey = self._e_hotkey.get().strip()

        if not hotkey:
            _safe_alert(self._win, "Champ manquant", "Le raccourci est obligatoire.")
            return

        tone_names = {t.name for t in self._tones}
        active_tone = self._cfg.active_tone if self._cfg.active_tone in tone_names else None
        mode = self._cfg.mode
        if mode == Mode.REWRITE_TONE and active_tone is None:
            mode = Mode.FIX_FRENCH

        try:
            cfg = self._cfg.model_copy(
                update={
                    "hotkey": hotkey,
                    "mode": mode,
                    "tones": self._tones,
                    "active_tone": active_tone,
                }
            )
            save_config(cfg)
        except Exception as exc:
            _safe_alert(self._win, "Erreur", str(exc))
            return

        self._on_save(cfg)
        self._win.destroy()


_TONE_EDITOR_WIDTH = 560
_TONE_EDITOR_HEIGHT = 500


class ToneEditor:
    def __init__(
        self,
        parent: ctk.CTkToplevel,
        index: int | None,
        tones: list[Tone],
        on_saved: Callable[[], None],
    ) -> None:
        self._tones = tones
        self._index = index
        self._on_saved = on_saved
        self._is_new = index is None

        title = "Ton personnalisé" if self._is_new else "Modifier le ton"

        self._win = ctk.CTkToplevel(parent)
        self._win.title(f"Plume — {title}")
        self._win.resizable(False, False)
        self._win.configure(fg_color=theme.DIALOG_BG)
        self._win.protocol("WM_DELETE_WINDOW", self._win.destroy)

        self._build(title)
        _center(self._win, _TONE_EDITOR_WIDTH, _TONE_EDITOR_HEIGHT)
        # On Windows the dialog opens without foreground activation (parent
        # widget HWND has WS_EX_NOACTIVATE), so the first click on any button
        # only activates the window. Force focus so clicks fire immediately.
        self._win.deiconify()
        self._win.lift()
        self._win.after(50, self._win.focus_force)
        self._win.after(80, self._win.grab_set)

    def _build(self, title: str) -> None:
        shell = ctk.CTkFrame(self._win, fg_color=theme.DIALOG_BG, corner_radius=0)
        shell.pack(fill="both", expand=True)

        frame = ctk.CTkFrame(shell, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=_PAD, pady=(theme.SP_20, _PAD))

        ctk.CTkLabel(
            frame,
            text=title,
            text_color=theme.TEXT_PRIMARY,
            font=_font(22, bold=True),
            anchor="w",
        ).pack(anchor="w", fill="x")
        _helper(
            frame,
            "Définis une instruction courte et réutilisable pour le mode Ton.",
        ).pack(anchor="w", fill="x", pady=(theme.SP_4, theme.SP_20))

        bar = ctk.CTkFrame(frame, fg_color="transparent")
        bar.pack(side="bottom", fill="x", pady=(theme.SP_20, 0))
        _secondary_button(bar, "Annuler", self._win.destroy).pack(side="left")
        _primary_button(bar, "Enregistrer", self._save).pack(side="right")

        card = _card(frame)
        card.pack(fill="both", expand=True)
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=_CARD_PAD, pady=_CARD_PAD)

        _field_label(form, "Nom affiché").pack(anchor="w", pady=(0, theme.SP_4), fill="x")
        self._e_name = _entry(form)
        self._e_name.pack(fill="x", pady=(0, theme.SP_16))

        _field_label(form, "Instruction").pack(anchor="w", pady=(0, theme.SP_4), fill="x")
        self._t_desc = ctk.CTkTextbox(
            form,
            fg_color=theme.ENTRY_BG,
            text_color=theme.TEXT_PRIMARY,
            border_color=theme.BORDER,
            border_width=1,
            corner_radius=theme.R_CONTROL,
            font=_font(12),
            height=170,
            wrap="word",
        )
        self._t_desc.pack(fill="both", expand=True)
        _helper(
            form,
            "Exemple : Rends le texte plus concis sans ajouter d'information nouvelle.",
        ).pack(anchor="w", fill="x", pady=(theme.SP_8, 0))

        if not self._is_new and self._index is not None:
            tone = self._tones[self._index]
            self._e_name.insert(0, tone.name)
            self._t_desc.insert("1.0", tone.description)

        self._e_name.focus_set()

    def _save(self) -> None:
        name = self._e_name.get().strip()
        desc = self._t_desc.get("1.0", "end").strip()
        if not name or not desc:
            _safe_alert(
                self._win, "Champs manquants", "Le nom et la description sont obligatoires."
            )
            return
        for i, existing in enumerate(self._tones):
            if existing.name == name and i != self._index:
                _safe_alert(self._win, "Nom en double", f"Un ton nommé « {name} » existe déjà.")
                return
        tone = Tone(name=name, description=desc)
        if self._index is None:
            self._tones.append(tone)
        else:
            self._tones[self._index] = tone
        self._on_saved()
        self._win.destroy()
