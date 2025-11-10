"""
Configuração centralizada usando Pydantic Settings
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Discord
    discord_token: str = Field(..., description="Token do bot Discord")
    discord_prefix: str = Field(default="!", description="Prefixo de comandos")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/cazalberto.db",
        description="URL de conexão do banco de dados",
    )

    # Audio
    audio_clips_path: Path = Field(
        default=Path("./audio_clips"), description="Diretório de clipes de áudio"
    )
    wow_ost_path: Path = Field(
        default=Path("./wow-ost"), description="Diretório de OST do WoW"
    )
    max_audio_size_mb: int = Field(default=10, description="Tamanho máximo de áudio em MB")

    # Web Panel
    web_host: str = Field(default="0.0.0.0", description="Host do painel web")
    web_port: int = Field(default=8080, description="Porta do painel web")
    web_reload: bool = Field(default=False, description="Hot reload no desenvolvimento")

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Nível de log"
    )
    log_file: Path = Field(
        default=Path("./logs/cazalberto.log"), description="Arquivo de log"
    )

    # Bot
    bot_version: str = Field(default="2.0.0", description="Versão do bot")
    command_prefix: str = Field(default="/", description="Prefixo de comandos slash")

    @field_validator("audio_clips_path", "wow_ost_path", "log_file", mode="before")
    @classmethod
    def convert_to_path(cls, v: str | Path) -> Path:
        """Converte strings em Path objects"""
        return Path(v) if isinstance(v, str) else v

    def ensure_directories(self) -> None:
        """Cria diretórios necessários se não existirem"""
        self.audio_clips_path.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        Path("./data").mkdir(parents=True, exist_ok=True)

    @property
    def database_path(self) -> Path:
        """Retorna o caminho do banco de dados SQLite"""
        if "sqlite" in self.database_url:
            # Extrai o caminho do arquivo da URL
            return Path(self.database_url.split("///")[-1])
        return Path("./data/cazalberto.db")


# Singleton global
_settings: Settings | None = None


def get_settings() -> Settings:
    """Retorna a instância singleton das configurações"""
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore
        _settings.ensure_directories()
    return _settings


# Atalho para uso direto
settings = get_settings()
