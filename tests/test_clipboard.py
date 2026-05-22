from __future__ import annotations

from unittest.mock import patch

import pyperclip
import pytest

from plume.clipboard import ClipboardError, get_clipboard, set_clipboard


def test_get_clipboard_returns_text() -> None:
    with patch("pyperclip.paste", return_value="Bonjour le monde"):
        assert get_clipboard() == "Bonjour le monde"


def test_get_clipboard_raises_on_empty() -> None:
    with patch("pyperclip.paste", return_value=""):
        with pytest.raises(ClipboardError, match="vide"):
            get_clipboard()


def test_get_clipboard_raises_on_missing_tool() -> None:
    with patch("pyperclip.paste", side_effect=pyperclip.PyperclipException("no tool")):
        with pytest.raises(ClipboardError, match="xclip"):
            get_clipboard()


def test_set_clipboard_calls_copy() -> None:
    with patch("pyperclip.copy") as mock_copy:
        set_clipboard("Bonjour le monde")
        mock_copy.assert_called_once_with("Bonjour le monde")


def test_set_clipboard_raises_on_missing_tool() -> None:
    with patch("pyperclip.copy", side_effect=pyperclip.PyperclipException("no tool")):
        with pytest.raises(ClipboardError, match="xclip"):
            set_clipboard("test")
