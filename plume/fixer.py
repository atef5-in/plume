from __future__ import annotations

import httpx

from plume.config import Config
from plume.prompts import SYSTEM_PROMPT

TIMEOUT = 30.0


class FixerError(Exception):
    pass


async def fix_text(text: str, cfg: Config) -> str:
    url = cfg.api_base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
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

    # Strip a single pair of surrounding straight or curly quotes if the model adds them
    if len(content) >= 2 and (
        (content[0] == '"' and content[-1] == '"')
        or (content[0] == "'" and content[-1] == "'")
        or (content[0] == "“" and content[-1] == "”")
    ):
        content = content[1:-1]

    return content
