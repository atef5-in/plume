from __future__ import annotations

import time

import pyperclip
from pynput.keyboard import Controller, Key

RELEASE_DELAY = 0.05   # seconds — let hotkey keys finish releasing
CAPTURE_DELAY = 0.15   # seconds — wait for target app to fill clipboard


def capture_selection() -> str:
    kbd = Controller()

    # Ensure modifier keys from the hotkey chord are released
    kbd.release(Key.ctrl)
    kbd.release(Key.alt)
    time.sleep(RELEASE_DELAY)

    with kbd.pressed(Key.ctrl):
        kbd.tap("c")

    time.sleep(CAPTURE_DELAY)

    try:
        return pyperclip.paste()
    except pyperclip.PyperclipException:
        return ""
