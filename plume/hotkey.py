from __future__ import annotations

from collections.abc import Callable

from pynput import keyboard


class GlobalHotkeyListener:
    def __init__(self, hotkey: str, callback: Callable[[], None]) -> None:
        self._hotkey = hotkey
        self._callback = callback
        self._listener: keyboard.GlobalHotKeys | None = None

    def start(self) -> None:
        self._listener = keyboard.GlobalHotKeys({self._hotkey: self._callback})
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
