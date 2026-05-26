from __future__ import annotations

import sys
import time
import tkinter as tk
from collections.abc import Callable

from PIL import Image, ImageDraw, ImageTk

from plume import theme
from plume.config import Mode

SIZE = 52
BG = theme.WIDGET_BG_KEY

# Render at higher resolution and downsample with LANCZOS for antialiased
# edges that pure tkinter Canvas ovals can't produce.
_RENDER_SCALE = 4

# Visual constants in window-pixel space (multiplied by _RENDER_SCALE internally)
_MARGIN = 3.0  # window edge → ring outer
_RING_W = 2.0  # idle/success/error ring thickness
_ARC_W = 3.0  # busy rotating arc thickness

# Timings
_BUSY_FPS_MS = 16
_BUSY_CYCLE_MS = 900
_BUSY_ARC_SWEEP_DEG = 110
_SUCCESS_HOLD_MS = 1500
_ERROR_HOLD_MS = 1500
_SHAKE_OFFSETS_PX = (3, -3, 2, -2, 0)
_SHAKE_STEP_MS = 44  # 5 × 44 ≈ 220ms


def _render_circle(
    ring_color: str,
    fill_color: str,
    arc: tuple[float, float] | None = None,
    arc_color: str | None = None,
) -> Image.Image:
    """Render the widget face at high res and downsample. Returns a SIZE×SIZE image."""
    s = SIZE * _RENDER_SCALE
    margin = _MARGIN * _RENDER_SCALE
    ring_w = _RING_W * _RENDER_SCALE
    arc_w = _ARC_W * _RENDER_SCALE

    img = Image.new("RGB", (s, s), BG)
    draw = ImageDraw.Draw(img)

    box = (margin, margin, s - margin, s - margin)
    draw.ellipse(box, fill=fill_color, outline=ring_color, width=int(ring_w))

    if arc is not None:
        start, end = arc
        ac = arc_color or ring_color
        # Arc sits on the ring centerline; keep same box.
        draw.arc(box, start=start, end=end, fill=ac, width=int(arc_w))

    return img.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


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
        self._mode = Mode.FIX_FRENCH

        self._state: str = "idle"  # idle | busy | success | error
        self._anim_job: str | None = None
        self._shake_job: str | None = None
        self._busy_t0_ms: float = 0.0

        # Kept as instance attrs so Tk does not GC the PhotoImage.
        self._tk_image: ImageTk.PhotoImage | None = None
        self._image_id: int | None = None
        self._label_id: int | None = None

        self._setup_window()
        self._build_canvas()
        self._render_idle()
        self._root.after(100, self._apply_circle_mask)

    # ── window setup ──────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 1.0)
        self._root.configure(bg=BG)
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        self._root.geometry(f"{SIZE}x{SIZE}+{sw - SIZE - 14}+{sh // 2 - SIZE // 2}")

    def _build_canvas(self) -> None:
        self._canvas = tk.Canvas(self._root, width=SIZE, height=SIZE, bg=BG, highlightthickness=0)
        self._canvas.pack()
        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._canvas.bind("<ButtonRelease-3>", self._on_right_release)
        self._canvas.bind("<Enter>", self._on_enter)
        self._canvas.bind("<Leave>", self._on_leave)

    # ── rendering primitives ──────────────────────────────────────────────────

    def _accent(self) -> tuple[str, str]:
        return theme.MODE_ACCENTS[self._mode]

    def _put_image(self, img: Image.Image) -> None:
        self._tk_image = ImageTk.PhotoImage(img)
        if self._image_id is None:
            self._image_id = self._canvas.create_image(SIZE // 2, SIZE // 2, image=self._tk_image)
        else:
            self._canvas.itemconfig(self._image_id, image=self._tk_image)

    def _put_label(self, text: str, color: str = theme.TEXT_PRIMARY, size: int = 12) -> None:
        font = (theme.ui_family(), size, "bold")
        if self._label_id is None:
            self._label_id = self._canvas.create_text(
                SIZE // 2, SIZE // 2, text=text, fill=color, font=font
            )
        else:
            self._canvas.itemconfig(self._label_id, text=text, fill=color, font=font)
        self._canvas.tag_raise(self._label_id)

    # ── per-state renderers ───────────────────────────────────────────────────

    def _render_idle(self) -> None:
        ring, fill = self._accent()
        if self._hovered:
            ring = theme.lighten(ring, 0.10)
            fill = theme.lighten(fill, 0.12)
        self._put_image(_render_circle(ring, fill))
        self._put_label(theme.MODE_LABELS[self._mode], size=12)

    def _render_busy_frame(self) -> None:
        ring_accent, fill = self._accent()
        # Dim the static ring so the bright arc reads as motion.
        dim_ring = fill  # ring blends into fill; only the arc shows
        t = (time.monotonic() * 1000 - self._busy_t0_ms) % _BUSY_CYCLE_MS
        tn = t / _BUSY_CYCLE_MS
        start = (tn * 360 - 90) % 360
        end = start + _BUSY_ARC_SWEEP_DEG
        img = _render_circle(dim_ring, fill, arc=(start, end), arc_color=ring_accent)
        self._put_image(img)
        self._put_label("")

    def _render_success(self) -> None:
        img = _render_circle(theme.SUCCESS, theme.SUCCESS_FILL)
        self._put_image(img)
        self._put_label("✓", color=theme.SUCCESS, size=18)

    def _render_error(self) -> None:
        img = _render_circle(theme.DANGER, theme.ERROR_FILL)
        self._put_image(img)
        self._put_label("!", color=theme.DANGER, size=20)

    # ── public state api ──────────────────────────────────────────────────────

    def set_idle(self) -> None:
        self._stop_anim()
        self._state = "idle"
        self._render_idle()

    def set_busy(self) -> None:
        self._stop_anim()
        self._state = "busy"
        self._busy_t0_ms = time.monotonic() * 1000
        self._tick_busy()

    def set_success(self) -> None:
        self._stop_anim()
        self._state = "success"
        self._render_success()
        self._anim_job = self._root.after(_SUCCESS_HOLD_MS, self.set_idle)

    def set_error(self) -> None:
        self._stop_anim()
        self._state = "error"
        self._render_error()
        self._start_shake()
        self._anim_job = self._root.after(_ERROR_HOLD_MS, self.set_idle)

    def update_mode(self, mode: Mode) -> None:
        self._mode = mode
        if self._state == "idle":
            self._render_idle()

    # ── animations ────────────────────────────────────────────────────────────

    def _tick_busy(self) -> None:
        self._render_busy_frame()
        self._anim_job = self._root.after(_BUSY_FPS_MS, self._tick_busy)

    def _stop_anim(self) -> None:
        if self._anim_job is not None:
            try:
                self._root.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None
        self._stop_shake()

    def _start_shake(self) -> None:
        base_x = self._root.winfo_x()
        base_y = self._root.winfo_y()

        def step(i: int) -> None:
            if i >= len(_SHAKE_OFFSETS_PX):
                self._shake_job = None
                return
            try:
                self._root.geometry(f"+{base_x + _SHAKE_OFFSETS_PX[i]}+{base_y}")
            except Exception:
                pass
            self._shake_job = self._root.after(_SHAKE_STEP_MS, lambda: step(i + 1))

        step(0)

    def _stop_shake(self) -> None:
        if self._shake_job is not None:
            try:
                self._root.after_cancel(self._shake_job)
            except Exception:
                pass
            self._shake_job = None

    # ── interaction ───────────────────────────────────────────────────────────

    def _on_enter(self, _e: tk.Event[tk.Canvas]) -> None:
        self._hovered = True
        if self._state == "idle":
            self._render_idle()

    def _on_leave(self, _e: tk.Event[tk.Canvas]) -> None:
        self._hovered = False
        if self._state == "idle":
            self._render_idle()

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

    # ── platform masks (preserved verbatim) ───────────────────────────────────

    def _apply_circle_mask(self) -> None:
        if sys.platform == "win32":
            self._apply_circle_mask_windows()
        else:
            self._apply_circle_mask_x11()

    def _apply_circle_mask_windows(self) -> None:
        try:
            self._root.wm_attributes("-transparentcolor", BG)
        except Exception:
            pass
        self._apply_noactivate_windows()

    def _apply_noactivate_windows(self) -> None:
        try:
            import ctypes

            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            windll = getattr(ctypes, "windll", None)
            if windll is None:
                return
            hwnd = windll.user32.GetParent(self._root.winfo_id())
            if not hwnd:
                hwnd = self._root.winfo_id()
            exstyle = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle | WS_EX_NOACTIVATE)
        except Exception:
            pass

    def _apply_circle_mask_x11(self) -> None:
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
            pass

    def position(self) -> tuple[int, int]:
        return self._root.winfo_x(), self._root.winfo_y()
