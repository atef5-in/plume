from __future__ import annotations

import subprocess


def notify(title: str, body: str, level: str = "normal") -> None:
    try:
        subprocess.run(
            ["notify-send", "-u", level, title, body],
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
