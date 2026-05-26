"""Shared customtkinter widget builders used by settings and wizard dialogs.

Centralizes button/entry/label/card construction so the two surfaces don't
drift apart visually.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox

import customtkinter as ctk

from plume import theme


def safe_alert(win: ctk.CTkToplevel, title: str, message: str) -> None:
    """Show an error messagebox without deadlocking a frameless+grab_set dialog.

    On Linux WMs, an `overrideredirect(True)` Toplevel that holds `grab_set()`
    will hang when a child messagebox tries to acquire input focus. Release the
    grab around the messagebox call, then reacquire it."""
    try:
        win.grab_release()
        messagebox.showerror(title, message, parent=win)
    finally:
        try:
            win.grab_set()
            win.focus_force()
        except tk.TclError:
            pass


def font(size: int = 11, bold: bool = False) -> ctk.CTkFont:
    return ctk.CTkFont(family=theme.ui_family(), size=size, weight="bold" if bold else "normal")


def primary_button(
    parent: ctk.CTkBaseClass,
    text: str,
    command: Callable[[], None],
    width: int = 110,
) -> ctk.CTkButton:
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=theme.BTN_PRIMARY_BG,
        hover_color=theme.BTN_PRIMARY_HOVER,
        text_color=theme.BTN_PRIMARY_FG,
        corner_radius=theme.R_CONTROL,
        border_width=0,
        height=32,
        width=width,
        font=font(12, bold=True),
    )


def secondary_button(
    parent: ctk.CTkBaseClass,
    text: str,
    command: Callable[[], None],
    width: int = 92,
) -> ctk.CTkButton:
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=theme.BTN_SECONDARY_BG,
        hover_color=theme.BTN_SECONDARY_HOVER,
        text_color=theme.BTN_SECONDARY_FG,
        corner_radius=theme.R_CONTROL,
        border_width=0,
        height=32,
        width=width,
        font=font(12),
    )


def card_action_button(
    parent: ctk.CTkBaseClass, text: str, command: Callable[[], None]
) -> ctk.CTkButton:
    """Smaller secondary button for card-header inline actions."""
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=theme.BTN_SECONDARY_BG,
        hover_color=theme.BTN_SECONDARY_HOVER,
        text_color=theme.BTN_SECONDARY_FG,
        corner_radius=theme.R_CONTROL,
        border_width=0,
        height=26,
        width=74,
        font=font(11),
    )


def entry(parent: ctk.CTkBaseClass, show: str = "") -> ctk.CTkEntry:
    return ctk.CTkEntry(
        parent,
        fg_color=theme.ENTRY_BG,
        text_color=theme.TEXT_PRIMARY,
        border_color=theme.BORDER,
        border_width=1,
        corner_radius=theme.R_CONTROL,
        height=38,
        font=font(12),
        show=show,
    )


def section_header(parent: ctk.CTkBaseClass, text: str) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        parent,
        text=text,
        text_color=theme.TEXT_MUTED,
        font=font(12, bold=True),
        anchor="w",
    )


def field_label(parent: ctk.CTkBaseClass, text: str) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        parent,
        text=text,
        text_color=theme.TEXT_SECONDARY,
        font=font(11),
        anchor="w",
    )


def helper(parent: ctk.CTkBaseClass, text: str, wraplength: int = 0) -> ctk.CTkLabel:
    kwargs = {"wraplength": wraplength} if wraplength else {}
    return ctk.CTkLabel(
        parent,
        text=text,
        text_color=theme.TEXT_MUTED,
        font=font(11),
        anchor="w",
        justify="left",
        **kwargs,
    )


def card(parent: ctk.CTkBaseClass) -> ctk.CTkFrame:
    return ctk.CTkFrame(
        parent,
        fg_color=theme.SURFACE_ELEVATED,
        border_width=0,
        corner_radius=theme.R_PANEL,
    )
