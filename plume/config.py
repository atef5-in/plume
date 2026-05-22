from __future__ import annotations

import tomllib
from enum import StrEnum
from pathlib import Path
from typing import Any

import tomli_w
from dotenv import dotenv_values
from platformdirs import user_config_dir
from pydantic import BaseModel, SecretStr, ValidationError

CONFIG_DIR: Path = Path(user_config_dir("plume"))

_DEFAULT_HOTKEY = "<ctrl>+<alt>+f"


class ConfigError(Exception):
    pass


class Mode(StrEnum):
    FIX_FRENCH = "fix_french"
    FIX_ENGLISH = "fix_english"
    TRANSLATE_FR_EN = "translate_fr_en"
    TRANSLATE_EN_FR = "translate_en_fr"


class Config(BaseModel):
    api_base_url: str
    api_key: SecretStr
    model: str
    hotkey: str = _DEFAULT_HOTKEY
    mode: Mode = Mode.FIX_FRENCH
    widget_position: tuple[int, int] | None = None


def _config_file() -> Path:
    return CONFIG_DIR / "config.toml"


def _env_file() -> Path:
    return CONFIG_DIR / ".env"


def load_config() -> Config:
    raw: dict[str, Any] = {}

    config_file = _config_file()
    if config_file.exists():
        with open(config_file, "rb") as f:
            raw = tomllib.load(f)

    env_vals = dotenv_values(_env_file())
    for env_key, field in (
        ("PLUME_API_KEY", "api_key"),
        ("PLUME_API_BASE_URL", "api_base_url"),
        ("PLUME_MODEL", "model"),
    ):
        val = env_vals.get(env_key)
        if val:
            raw.setdefault(field, val)

    try:
        return Config.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"Invalid or missing config: {exc}") from exc


def save_config(cfg: Config) -> None:
    config_dir = CONFIG_DIR
    config_dir.mkdir(parents=True, exist_ok=True)

    data: dict[str, Any] = {
        "api_base_url": cfg.api_base_url,
        "model": cfg.model,
        "hotkey": cfg.hotkey,
        "mode": cfg.mode.value,
    }
    if cfg.widget_position is not None:
        data["widget_position"] = list(cfg.widget_position)

    with open(_config_file(), "wb") as f:
        tomli_w.dump(data, f)

    _env_file().write_text(
        f"PLUME_API_KEY={cfg.api_key.get_secret_value()}\n",
        encoding="utf-8",
    )
