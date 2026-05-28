from __future__ import annotations

from pathlib import Path

import pytest

import plume.config as config_module
from plume.config import (
    Config,
    Mode,
    Tone,
    load_config,
    save_config,
)

_TEST_URL = "https://test-sigma.example/v1"
_TEST_KEY = "sk-test-fake-key"
_TEST_MODEL = "test-model"


@pytest.fixture(autouse=True)
def isolated_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module, "CONFIG_DIR", tmp_path)
    # Stub out the bundled secrets loader so tests don't depend on the real
    # sigma_secrets.env that ships with the build.
    monkeypatch.setattr(
        config_module,
        "_load_sigma_secrets",
        lambda: (_TEST_URL, _TEST_KEY, _TEST_MODEL),
    )


def _make_cfg(**overrides: object) -> Config:
    base: dict[str, object] = {
        "api_base_url": _TEST_URL,
        "api_key": _TEST_KEY,
        "model": _TEST_MODEL,
    }
    base.update(overrides)
    return Config(**base)  # type: ignore[arg-type]


def test_roundtrip_basic() -> None:
    save_config(_make_cfg())
    loaded = load_config()

    assert loaded.api_base_url == _TEST_URL
    assert loaded.api_key.get_secret_value() == _TEST_KEY
    assert loaded.model == _TEST_MODEL
    assert loaded.hotkey == "<ctrl>+<alt>+f"
    assert loaded.widget_position is None


def test_roundtrip_with_position() -> None:
    save_config(_make_cfg(widget_position=(120, 340)))
    loaded = load_config()
    assert loaded.widget_position == (120, 340)


def test_sigma_constants_are_locked_on_load(tmp_path: Path) -> None:
    # Even if config.toml on disk had different values, load_config must
    # always return the locked Sigma constants.
    (tmp_path / "config.toml").write_text(
        'api_base_url = "https://attacker.example/v1"\n'
        'model = "evil-model"\n'
        'hotkey = "<ctrl>+<alt>+f"\n'
        'mode = "fix_french"\n',
        encoding="utf-8",
    )
    loaded = load_config()
    assert loaded.api_base_url == _TEST_URL
    assert loaded.model == _TEST_MODEL
    assert loaded.api_key.get_secret_value() == _TEST_KEY


def test_api_fields_not_written_to_toml(tmp_path: Path) -> None:
    save_config(_make_cfg())
    toml_text = (tmp_path / "config.toml").read_text()
    assert "api_base_url" not in toml_text
    assert "api_key" not in toml_text
    assert "model" not in toml_text
    assert _TEST_KEY not in toml_text
    # .env is no longer written by the Sigma build.
    assert not (tmp_path / ".env").exists()


def test_load_without_config_file_returns_sigma_defaults() -> None:
    # No config.toml on disk — load_config still works because the locked
    # constants supply the required fields.
    loaded = load_config()
    assert loaded.api_base_url == _TEST_URL
    assert loaded.api_key.get_secret_value() == _TEST_KEY
    assert loaded.model == _TEST_MODEL


def test_tones_roundtrip() -> None:
    save_config(
        _make_cfg(
            mode=Mode.REWRITE_TONE,
            tones=[
                Tone(name="Pro", description="ton professionnel"),
                Tone(name="Concis", description="phrases courtes, factuel"),
            ],
            active_tone="Pro",
        )
    )
    loaded = load_config()
    assert loaded.mode == Mode.REWRITE_TONE
    assert [t.name for t in loaded.tones] == ["Pro", "Concis"]
    assert loaded.tones[0].description == "ton professionnel"
    assert loaded.active_tone == "Pro"


def test_custom_hotkey_survives_roundtrip() -> None:
    save_config(_make_cfg(hotkey="<ctrl>+<shift>+x"))
    loaded = load_config()
    assert loaded.hotkey == "<ctrl>+<shift>+x"
