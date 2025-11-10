"""
Testes para configuração
"""

from pathlib import Path

from src.cazalberto.core.config import Settings


def test_default_settings() -> None:
    """Testa valores padrão das configurações"""
    settings = Settings(discord_token="test_token")  # type: ignore

    assert settings.discord_token == "test_token"
    assert settings.discord_prefix == "!"
    assert settings.web_port == 8080
    assert settings.log_level == "INFO"
    assert settings.bot_version == "2.0.0"


def test_path_conversion() -> None:
    """Testa conversão de strings para Path"""
    settings = Settings(
        discord_token="test",  # type: ignore
        audio_clips_path="./test_audio",
        log_file="./logs/test.log",
    )

    assert isinstance(settings.audio_clips_path, Path)
    assert isinstance(settings.log_file, Path)


def test_database_path() -> None:
    """Testa extração do caminho do banco de dados"""
    settings = Settings(
        discord_token="test",  # type: ignore
        database_url="sqlite+aiosqlite:///./data/test.db",
    )

    db_path = settings.database_path
    assert isinstance(db_path, Path)
    assert str(db_path) == "./data/test.db"
