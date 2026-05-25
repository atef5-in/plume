from __future__ import annotations

import pyperclip


class ClipboardError(Exception):
    pass


def get_clipboard() -> str:
    try:
        text: str = pyperclip.paste()
    except pyperclip.PyperclipException as exc:
        raise ClipboardError(
            "Impossible d'accéder au presse-papiers. Installez xclip : sudo apt-get install xclip"
        ) from exc
    if not text:
        raise ClipboardError("Le presse-papiers est vide.")
    return text


def set_clipboard(text: str) -> None:
    try:
        pyperclip.copy(text)
    except pyperclip.PyperclipException as exc:
        raise ClipboardError(
            "Impossible d'écrire dans le presse-papiers. "
            "Installez xclip : sudo apt-get install xclip"
        ) from exc
