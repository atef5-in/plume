from __future__ import annotations

from pathlib import Path

import pytest

import plume.config as config_module
from plume.config import Config, ConfigError, load_config, save_config


@pytest.fixture(autouse=True)
def isolated_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module, "CONFIG_DIR", tmp_path)


def test_roundtrip_basic() -> None:
    cfg = Config(
        api_base_url="https://example.com/v1",
        api_key="s3cr3t",
        model="test-model",
    )
    save_config(cfg)
    loaded = load_config()

    assert loaded.api_base_url == "https://example.com/v1"
    assert loaded.api_key.get_secret_value() == "s3cr3t"
    assert loaded.model == "test-model"
    assert loaded.hotkey == "<ctrl>+<alt>+f"
    assert loaded.widget_position is None


def test_roundtrip_with_position() -> None:
    cfg = Config(
        api_base_url="https://example.com/v1",
        api_key="s3cr3t",
        model="test-model",
        widget_position=(120, 340),
    )
    save_config(cfg)
    loaded = load_config()

    assert loaded.widget_position == (120, 340)


def test_api_key_not_in_toml(tmp_path: Path) -> None:
    cfg = Config(
        api_base_url="https://example.com/v1",
        api_key="super-secret",
        model="m",
    )
    save_config(cfg)

    toml_text = (tmp_path / "config.toml").read_text()
    assert "super-secret" not in toml_text

    env_text = (tmp_path / ".env").read_text()
    assert "super-secret" in env_text


def test_load_missing_required_fields() -> None:
    # No config.toml, no .env → must raise ConfigError
    with pytest.raises(ConfigError):
        load_config()


def test_custom_hotkey_survives_roundtrip() -> None:
    cfg = Config(
        api_base_url="https://example.com/v1",
        api_key="k",
        model="m",
        hotkey="<ctrl>+<shift>+x",
    )
    save_config(cfg)
    loaded = load_config()
    assert loaded.hotkey == "<ctrl>+<shift>+x"
