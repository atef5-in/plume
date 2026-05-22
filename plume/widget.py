from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

SIZE = 56
COLOR_IDLE = "#4A90E2"
COLOR_BUSY = "#E2914A"
COLOR_SUCCESS = "#5CB85C"
BG = "#1a1a1a"
ALPHA_NORMAL = 0.75
ALPHA_HOVER = 1.0


class FloatingWidget:
    def __init__(self, root: tk.Tk, on_click: Callable[[], None]) -> None:
        self._root = root
        self._on_click = on_click
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._dragging = False

        self._setup_window()
        self._build_canvas()

    def _setup_window(self) -> None:
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", ALPHA_NORMAL)
        self._root.configure(bg=BG)

        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x = sw - SIZE - 12
        y = sh // 2 - SIZE // 2
        self._root.geometry(f"{SIZE}x{SIZE}+{x}+{y}")

    def _build_canvas(self) -> None:
        self._canvas = tk.Canvas(
            self._root, width=SIZE, height=SIZE, bg=BG, highlightthickness=0
        )
        self._canvas.pack()

        pad = 4
        self._circle = self._canvas.create_oval(
            pad, pad, SIZE - pad, SIZE - pad, fill=COLOR_IDLE, outline=""
        )
        self._label = self._canvas.create_text(
            SIZE // 2, SIZE // 2, text="P", fill="white", font=("Arial", 18, "bold")
        )

        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._canvas.bind("<Enter>", lambda _e: self._root.attributes("-alpha", ALPHA_HOVER))
        self._canvas.bind("<Leave>", lambda _e: self._root.attributes("-alpha", ALPHA_NORMAL))

    def _on_press(self, event: tk.Event[tk.Canvas]) -> None:
        self._drag_start_x = event.x_root - self._root.winfo_x()
        self._drag_start_y = event.y_root - self._root.winfo_y()
        self._dragging = False

    def _on_drag(self, event: tk.Event[tk.Canvas]) -> None:
        self._dragging = True
        x = event.x_root - self._drag_start_x
        y = event.y_root - self._drag_start_y
        self._root.geometry(f"+{x}+{y}")

    def _on_release(self, event: tk.Event[tk.Canvas]) -> None:
        if not self._dragging:
            self._on_click()

    def set_busy(self) -> None:
        self._canvas.itemconfig(self._circle, fill=COLOR_BUSY)
        self._canvas.itemconfig(self._label, text="…")

    def set_idle(self) -> None:
        self._canvas.itemconfig(self._circle, fill=COLOR_IDLE)
        self._canvas.itemconfig(self._label, text="P")

    def set_success(self) -> None:
        self._canvas.itemconfig(self._circle, fill=COLOR_SUCCESS)
        self._canvas.itemconfig(self._label, text="✓")
        self._root.after(1500, self.set_idle)

    def position(self) -> tuple[int, int]:
        return self._root.winfo_x(), self._root.winfo_y()
