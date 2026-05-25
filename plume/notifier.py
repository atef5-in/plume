from __future__ import annotations

import os
import subprocess
import sys


def _windows_icon_path() -> str | None:
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    path = os.path.join(base, "plume.ico")
    return path if os.path.isfile(path) else None


def notify(title: str, body: str, level: str = "normal") -> None:
    if sys.platform == "win32":
        _notify_windows(title, body)
    else:
        _notify_linux(title, body, level)


def _notify_linux(title: str, body: str, level: str) -> None:
    try:
        subprocess.run(
            ["notify-send", "-u", level, title, body],
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def _notify_windows(title: str, body: str) -> None:
    try:
        from plyer import notification

        icon = _windows_icon_path()
        kwargs: dict[str, object] = {
            "title": title,
            "message": body,
            "app_name": "Plume",
            "timeout": 5,
        }
        if icon:
            kwargs["app_icon"] = icon
        notification.notify(**kwargs)
    except Exception:
        pass
