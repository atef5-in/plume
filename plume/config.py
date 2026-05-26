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
    REWRITE_TONE = "rewrite_tone"


class Tone(BaseModel):
    name: str
    description: str


# Seeded into a fresh install so the user immediately has working tones.
# Editable/deletable through the settings dialog like any user-defined tone.
DEFAULT_TONES: list[Tone] = [
    Tone(
        name="Plus formel",
        description=(
            "Réécris le texte dans un registre plus formel et soutenu. "
            "Garde exactement le même sens, ne change aucun fait, "
            "préserve les dates, chiffres et noms à l'identique."
        ),
    ),
    Tone(
        name="Plus court",
        description=(
            "Réécris en formulations plus courtes et économes. "
            "Garde toutes les informations du texte original — "
            "aucune ne doit disparaître. Ne change pas le sens."
        ),
    ),
    Tone(
        name="Plus long",
        description=(
            "Développe le texte avec un peu plus de détails et de précision "
            "à partir de ce qui est déjà présent. N'invente aucune information "
            "qui ne soit pas dans le texte d'origine."
        ),
    ),
    Tone(
        name="Plus direct",
        description=(
            "Réécris de façon plus directe et concrète, en allant droit à "
            "l'essentiel. Supprime les formules de politesse superflues "
            "mais garde tous les faits, dates et chiffres."
        ),
    ),
    Tone(
        name="Amical",
        description=(
            "Réécris dans un ton plus chaleureux et amical, en tutoyant "
            "si le texte d'origine tutoyait, en vouvoyant sinon. "
            "Garde le sens et toutes les informations."
        ),
    ),
]


class Config(BaseModel):
    api_base_url: str
    api_key: SecretStr
    model: str
    hotkey: str = _DEFAULT_HOTKEY
    mode: Mode = Mode.FIX_FRENCH
    widget_position: tuple[int, int] | None = None
    tones: list[Tone] = []
    active_tone: str | None = None


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
    if cfg.tones:
        data["tones"] = [{"name": t.name, "description": t.description} for t in cfg.tones]
    if cfg.active_tone is not None:
        data["active_tone"] = cfg.active_tone

    with open(_config_file(), "wb") as f:
        tomli_w.dump(data, f)

    _env_file().write_text(
        f"PLUME_API_KEY={cfg.api_key.get_secret_value()}\n",
        encoding="utf-8",
    )
