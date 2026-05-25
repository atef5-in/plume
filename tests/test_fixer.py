from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from plume.config import Config, Mode, Tone
from plume.fixer import FixerError, fix_text

_BASE = "https://test.example.com/v1"


@pytest.fixture
def cfg() -> Config:
    return Config(
        api_base_url=_BASE,
        api_key="test-key",
        model="test-model",
    )


def _llm_response(content: str) -> dict[str, object]:
    return {"choices": [{"message": {"content": content}}]}


async def test_happy_path(httpx_mock: HTTPXMock, cfg: Config) -> None:
    httpx_mock.add_response(json=_llm_response("Bonjour, ça va ?"))
    result = await fix_text("Bonjour, ca va?", cfg)
    assert result == "Bonjour, ça va ?"


async def test_strips_double_quotes(httpx_mock: HTTPXMock, cfg: Config) -> None:
    httpx_mock.add_response(json=_llm_response('"Bonjour, ça va ?"'))
    result = await fix_text("Bonjour, ca va?", cfg)
    assert result == "Bonjour, ça va ?"


async def test_strips_single_quotes(httpx_mock: HTTPXMock, cfg: Config) -> None:
    httpx_mock.add_response(json=_llm_response("'Bonjour, ça va ?'"))
    result = await fix_text("Bonjour, ca va?", cfg)
    assert result == "Bonjour, ça va ?"


async def test_http_401(httpx_mock: HTTPXMock, cfg: Config) -> None:
    httpx_mock.add_response(status_code=401, text="Unauthorized")
    with pytest.raises(FixerError, match="401"):
        await fix_text("test", cfg)


async def test_http_500(httpx_mock: HTTPXMock, cfg: Config) -> None:
    httpx_mock.add_response(status_code=500, text="Internal Server Error")
    with pytest.raises(FixerError, match="500"):
        await fix_text("test", cfg)


async def test_timeout(httpx_mock: HTTPXMock, cfg: Config) -> None:
    httpx_mock.add_exception(httpx.ConnectTimeout("connection timed out"))
    with pytest.raises(FixerError, match="timed out"):
        await fix_text("test", cfg)


async def test_url_constructed_correctly(httpx_mock: HTTPXMock, cfg: Config) -> None:
    httpx_mock.add_response(json=_llm_response("ok"))
    await fix_text("test", cfg)
    request = httpx_mock.get_request()
    assert request is not None
    assert str(request.url) == f"{_BASE}/chat/completions"


async def test_strips_preamble(httpx_mock: HTTPXMock, cfg: Config) -> None:
    httpx_mock.add_response(json=_llm_response("Voici le texte corrigé :\n\nBonjour, ça va ?"))
    result = await fix_text("Bonjour, ca va?", cfg)
    assert result == "Bonjour, ça va ?"


async def test_auth_header_sent(httpx_mock: HTTPXMock, cfg: Config) -> None:
    httpx_mock.add_response(json=_llm_response("ok"))
    await fix_text("test", cfg)
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer test-key"


async def test_rewrite_tone_sends_tone_description(httpx_mock: HTTPXMock) -> None:
    import json as _json

    cfg = Config(
        api_base_url=_BASE,
        api_key="test-key",
        model="test-model",
        tones=[Tone(name="Pro", description="ton professionnel, courtois")],
        active_tone="Pro",
    )
    httpx_mock.add_response(json=_llm_response("réécrit"))
    await fix_text("texte source", cfg, Mode.REWRITE_TONE)
    request = httpx_mock.get_request()
    assert request is not None
    body = _json.loads(request.content)
    system_msg = body["messages"][0]["content"]
    assert "ton professionnel, courtois" in system_msg


async def test_rewrite_tone_missing_active_tone(cfg: Config) -> None:
    with pytest.raises(FixerError, match="Aucun ton"):
        await fix_text("test", cfg, Mode.REWRITE_TONE)


async def test_rewrite_tone_unknown_active_tone() -> None:
    cfg = Config(
        api_base_url=_BASE,
        api_key="test-key",
        model="test-model",
        tones=[Tone(name="Pro", description="x")],
        active_tone="Missing",
    )
    with pytest.raises(FixerError, match="introuvable"):
        await fix_text("test", cfg, Mode.REWRITE_TONE)
