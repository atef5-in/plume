from __future__ import annotations

import subprocess
import sys


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

        notification.notify(title=title, message=body, app_name="Plume", timeout=5)
    except Exception:
        pass
