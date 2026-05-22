from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from plume.config import Mode

SIZE = 52
BG = "#0d0d0d"
ALPHA_NORMAL = 0.82
ALPHA_HOVER = 1.0

# Idle colors per mode: (ring, fill, fill-hover)
_MODE_COLORS: dict[Mode, tuple[str, str, str]] = {
    Mode.FIX_FRENCH:      ("#6366f1", "#312e81", "#3730a3"),  # indigo
    Mode.FIX_ENGLISH:     ("#2563eb", "#1e3a8a", "#1e40af"),  # blue
    Mode.TRANSLATE_FR_EN: ("#d97706", "#78350f", "#92400e"),  # amber
    Mode.TRANSLATE_EN_FR: ("#7c3aed", "#3b0764", "#4c1d95"),  # purple
}

# Short label displayed on the circle per mode
_MODE_LABELS: dict[Mode, str] = {
    Mode.FIX_FRENCH:      "FR",
    Mode.FIX_ENGLISH:     "EN",
    Mode.TRANSLATE_FR_EN: "F›E",
    Mode.TRANSLATE_EN_FR: "E›F",
}

# Busy pulse: dark fill, animated ring
_FILL_BUSY = "#1e1b4b"
_PULSE_STEPS = ["#6366f1", "#818cf8", "#a5b4fc", "#c7d2fe", "#e0e7ff",
                "#ffffff", "#e0e7ff", "#c7d2fe", "#a5b4fc", "#818cf8"]
_PULSE_MS = 90

_FILL_SUCCESS = "#059669"  # emerald
_RING_SUCCESS = "#34d399"

_RING_W = 3   # ring thickness in pixels
_PAD = 5      # gap between window edge and ring outer boundary


class FloatingWidget:
    def __init__(
        self,
        root: tk.Tk,
        on_click: Callable[[], None],
        on_right_click: Callable[[int, int], None] | None = None,
    ) -> None:
        self._root = root
        self._on_click = on_click
        self._on_right_click = on_right_click
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._dragging = False
        self._hovered = False
        self._pulse_job: str | None = None
        self._pulse_step = 0
        self._mode = Mode.FIX_FRENCH

        self._setup_window()
        self._build_canvas()
        self._draw_idle()
        self._root.after(100, self._apply_circle_mask)

    def _setup_window(self) -> None:
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", ALPHA_NORMAL)
        self._root.configure(bg=BG)
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        self._root.geometry(f"{SIZE}x{SIZE}+{sw - SIZE - 14}+{sh // 2 - SIZE // 2}")

    def _build_canvas(self) -> None:
        self._canvas = tk.Canvas(
            self._root, width=SIZE, height=SIZE, bg=BG, highlightthickness=0
        )
        self._canvas.pack()
        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._canvas.bind("<ButtonRelease-3>", self._on_right_release)
        self._canvas.bind("<Enter>", self._on_enter)
        self._canvas.bind("<Leave>", self._on_leave)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _oval(self, pad: int, fill: str, tag: str) -> int:
        return self._canvas.create_oval(pad, pad, SIZE - pad, SIZE - pad,
                                        fill=fill, outline="", tags=tag)

    def _ring(self, pad: int, color: str, tag: str) -> int:
        return self._canvas.create_oval(pad, pad, SIZE - pad, SIZE - pad,
                                        fill="", outline=color, width=_RING_W, tags=tag)

    def _text(self, content: str, tag: str, size: int = 14) -> int:
        return self._canvas.create_text(
            SIZE // 2, SIZE // 2,
            text=content, fill="#ffffff",
            font=("Arial", size, "bold"),
            tags=tag,
        )

    def _clear(self) -> None:
        self._canvas.delete("all")

    def _ring_color(self) -> str:
        return _MODE_COLORS[self._mode][0]

    def _fill_color(self) -> str:
        return _MODE_COLORS[self._mode][2 if self._hovered else 1]

    # ── states ────────────────────────────────────────────────────────────────

    def _draw_idle(self) -> None:
        self._clear()
        self._oval(_PAD, self._ring_color(), "ring_bg")
        self._oval(_PAD + _RING_W, self._fill_color(), "fill")
        self._text(_MODE_LABELS[self._mode], "label")

    def set_idle(self) -> None:
        self._stop_pulse()
        self._draw_idle()

    def set_busy(self) -> None:
        self._stop_pulse()
        self._clear()
        self._oval(_PAD, _PULSE_STEPS[0], "ring_bg")
        self._oval(_PAD + _RING_W, _FILL_BUSY, "fill")
        self._text("…", "label", size=18)
        self._pulse_step = 0
        self._tick_pulse()

    def set_success(self) -> None:
        self._stop_pulse()
        self._clear()
        self._oval(_PAD, _RING_SUCCESS, "ring_bg")
        self._oval(_PAD + _RING_W, _FILL_SUCCESS, "fill")
        self._text("✓", "label")
        self._root.after(1500, self.set_idle)

    def update_mode(self, mode: Mode) -> None:
        self._mode = mode
        self._draw_idle()

    # ── pulse ─────────────────────────────────────────────────────────────────

    def _tick_pulse(self) -> None:
        color = _PULSE_STEPS[self._pulse_step % len(_PULSE_STEPS)]
        self._canvas.itemconfig("ring_bg", fill=color)
        self._pulse_step += 1
        self._pulse_job = self._root.after(_PULSE_MS, self._tick_pulse)

    def _stop_pulse(self) -> None:
        if self._pulse_job is not None:
            self._root.after_cancel(self._pulse_job)
            self._pulse_job = None

    # ── interaction ───────────────────────────────────────────────────────────

    def _on_enter(self, _e: tk.Event[tk.Canvas]) -> None:
        self._hovered = True
        self._root.attributes("-alpha", ALPHA_HOVER)
        self._canvas.itemconfig("fill", fill=_MODE_COLORS[self._mode][2])

    def _on_leave(self, _e: tk.Event[tk.Canvas]) -> None:
        self._hovered = False
        self._root.attributes("-alpha", ALPHA_NORMAL)
        self._canvas.itemconfig("fill", fill=_MODE_COLORS[self._mode][1])

    def _on_press(self, event: tk.Event[tk.Canvas]) -> None:
        self._drag_start_x = event.x_root - self._root.winfo_x()
        self._drag_start_y = event.y_root - self._root.winfo_y()
        self._dragging = False

    def _on_drag(self, event: tk.Event[tk.Canvas]) -> None:
        self._dragging = True
        self._root.geometry(
            f"+{event.x_root - self._drag_start_x}+{event.y_root - self._drag_start_y}"
        )

    def _on_release(self, _e: tk.Event[tk.Canvas]) -> None:
        if not self._dragging:
            self._on_click()

    def _on_right_release(self, e: tk.Event[tk.Canvas]) -> None:
        if self._on_right_click is not None:
            self._on_right_click(e.x_root, e.y_root)

    def _apply_circle_mask(self) -> None:
        try:
            import Xlib.display
            from Xlib.ext import shape as xshape

            self._root.update()
            dpy = Xlib.display.Display()
            screen = dpy.screen()
            win = dpy.create_resource_object("window", self._root.winfo_id())

            pm = screen.root.create_pixmap(SIZE, SIZE, 1)
            gc = pm.create_gc(foreground=0, background=0)
            pm.fill_rectangle(gc, 0, 0, SIZE, SIZE)
            gc.change(foreground=1)
            pm.poly_fill_arc(gc, [(0, 0, SIZE, SIZE, 0, 360 * 64)])

            win.shape_mask(xshape.SO.Set, xshape.SK.Bounding, 0, 0, pm)
            pm.free()
            gc.free()
            dpy.flush()
        except Exception:
            pass  # shape extension unavailable — corners stay, no crash

    def position(self) -> tuple[int, int]:
        return self._root.winfo_x(), self._root.winfo_y()
