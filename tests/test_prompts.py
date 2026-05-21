from __future__ import annotations

from plume.prompts import SYSTEM_PROMPT


def test_key_phrase_no_meaning_change() -> None:
    assert "Ne change JAMAIS le sens" in SYSTEM_PROMPT


def test_key_phrase_no_added_info() -> None:
    assert "N'ajoute AUCUNE information" in SYSTEM_PROMPT


def test_no_markdown_fences() -> None:
    assert "```" not in SYSTEM_PROMPT


def test_is_non_empty_string() -> None:
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 100
