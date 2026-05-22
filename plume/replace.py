from __future__ import annotations

import time

import pyperclip
from pynput.keyboard import Controller, Key

PASTE_DELAY = 0.05  # seconds — let clipboard settle before Ctrl+V


def replace_selection(text: str) -> None:
    kbd = Controller()
    pyperclip.copy(text)
    time.sleep(PASTE_DELAY)
    with kbd.pressed(Key.ctrl):
        kbd.tap("v")
