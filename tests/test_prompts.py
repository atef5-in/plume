from __future__ import annotations

from plume.prompts import SYSTEM_PROMPT, get_rewrite_prompt


def test_key_phrase_no_meaning_change() -> None:
    assert "Ne change JAMAIS le sens" in SYSTEM_PROMPT


def test_key_phrase_no_added_info() -> None:
    assert "N'ajoute AUCUNE information" in SYSTEM_PROMPT


def test_no_markdown_fences() -> None:
    assert "```" not in SYSTEM_PROMPT


def test_is_non_empty_string() -> None:
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 100


def test_rewrite_prompt_contains_description() -> None:
    prompt = get_rewrite_prompt("ton concis et factuel")
    assert "ton concis et factuel" in prompt


def test_rewrite_prompt_strict_fidelity_rules() -> None:
    prompt = get_rewrite_prompt("amical")
    assert "ne restructure pas" in prompt.lower()
    assert "n'ajoute aucune information" in prompt.lower()
