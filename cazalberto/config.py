"""Configuração do bot, lida de variáveis de ambiente (e do arquivo .env)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class ConfigError(Exception):
    """Configuração inválida ou ausente."""


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


def _env_path(name: str, default: str, base: Path) -> Path:
    path = Path(os.getenv(name) or default).expanduser()
    return path if path.is_absolute() else base / path


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} precisa ser um número inteiro (recebido: {value!r})") from exc


@dataclass(frozen=True)
class Settings:
    token: str
    command_prefix: str
    data_dir: Path
    audio_dir: Path
    wow_dir: Path | None
    sync_on_startup: bool
    dev_guild_id: int | None
    log_level: str
    log_file: Path | None
    max_download_mb: int

    @property
    def commands_file(self) -> Path:
        return self.data_dir / "commands.json"

    @property
    def playlists_file(self) -> Path:
        return self.data_dir / "playlists.json"

    @property
    def jokes_file(self) -> Path:
        return self.data_dir / "jokes.json"

    @property
    def wow_enabled(self) -> bool:
        return self.wow_dir is not None and self.wow_dir.is_dir()

    @classmethod
    def from_env(cls, *, base_dir: Path = PROJECT_ROOT, require_token: bool = True) -> Settings:
        load_dotenv(base_dir / ".env")

        token = (os.getenv("DISCORD_TOKEN") or "").strip()
        if require_token and not token:
            raise ConfigError(
                "DISCORD_TOKEN não configurado. Crie um arquivo .env (veja .env.example) "
                "ou defina a variável de ambiente."
            )

        wow_dir: Path | None = None
        if os.getenv("WOW_OST_DIR"):
            wow_dir = _env_path("WOW_OST_DIR", "", base_dir)
        elif (base_dir / "wow-music").is_dir():
            wow_dir = base_dir / "wow-music"

        guild = os.getenv("DEV_GUILD_ID")
        log_file = os.getenv("LOG_FILE", "bot.log").strip()

        return cls(
            token=token,
            command_prefix=os.getenv("COMMAND_PREFIX", "!"),
            data_dir=_env_path("DATA_DIR", "data", base_dir),
            audio_dir=_env_path("AUDIO_DIR", "audio_clips", base_dir),
            wow_dir=wow_dir,
            sync_on_startup=_env_bool("SYNC_ON_STARTUP"),
            dev_guild_id=int(guild) if guild and guild.isdigit() else None,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            log_file=(base_dir / log_file) if log_file else None,
            max_download_mb=_env_int("MAX_DOWNLOAD_MB", 10),
        )
