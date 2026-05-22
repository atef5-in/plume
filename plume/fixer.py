from __future__ import annotations

import httpx

from plume.config import Config, Mode
from plume.prompts import get_prompt

TIMEOUT = 30.0

_PREAMBLE_MARKERS = (
    # French fix preambles
    "voici le texte corrig",
    "texte corrig",
    "voici la correction",
    "voici le résultat",
    "voici le resultat",
    # English fix preambles
    "here is the corrected",
    "here's the corrected",
    "corrected text:",
    # Translation preambles
    "here is the translation",
    "here's the translation",
    "voici la traduction",
    "traduction :",
    "translation:",
)


class FixerError(Exception):
    pass


def _strip_markdown(text: str) -> str:
    import re
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # **bold**
    text = re.sub(r"\*(.+?)\*", r"\1", text)       # *italic*
    text = re.sub(r"__(.+?)__", r"\1", text)       # __bold__
    text = re.sub(r"_(.+?)_", r"\1", text)         # _italic_
    return text


def _strip_preamble(text: str) -> str:
    first_line = text.split("\n")[0].rstrip(" :").lower()
    if any(first_line.startswith(marker) for marker in _PREAMBLE_MARKERS):
        rest = text.split("\n", 1)[1].lstrip("\n")
        return rest if rest else text
    return text


def _strip_surrounding_quotes(text: str) -> str:
    if len(text) < 2:
        return text
    pairs = [('"', '"'), ("'", "'"), ("“", "”")]
    for open_q, close_q in pairs:
        if text[0] == open_q and text[-1] == close_q:
            return text[1:-1]
    return text


async def fix_text(text: str, cfg: Config, mode: Mode = Mode.FIX_FRENCH) -> str:
    url = cfg.api_base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": get_prompt(mode)},
            {"role": "user", "content": text},
        ],
        "temperature": 0.1,
        "max_tokens": 2048,
    }
    headers = {
        "Authorization": f"Bearer {cfg.api_key.get_secret_value()}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise FixerError("LLM request timed out") from exc
    except httpx.ConnectError as exc:
        raise FixerError(f"Cannot connect to {url} — check the base URL and your network") from exc
    except httpx.HTTPStatusError as exc:
        raise FixerError(f"HTTP {exc.response.status_code}: {exc.response.text[:120]}") from exc

    data: dict[str, object] = response.json()
    choices = data["choices"]
    assert isinstance(choices, list)
    first = choices[0]
    assert isinstance(first, dict)
    message = first["message"]
    assert isinstance(message, dict)
    content = message["content"]
    assert isinstance(content, str)

    content = content.strip()
    content = _strip_surrounding_quotes(content)
    content = _strip_preamble(content)
    content = _strip_markdown(content)

    return content
