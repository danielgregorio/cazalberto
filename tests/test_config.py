import pytest

from cazalberto.config import ConfigError, Settings

ENV_VARS = [
    "DISCORD_TOKEN",
    "WOW_OST_DIR",
    "DATA_DIR",
    "AUDIO_DIR",
    "SYNC_ON_STARTUP",
    "DEV_GUILD_ID",
    "MAX_DOWNLOAD_MB",
    "LOG_FILE",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_missing_token(tmp_path):
    with pytest.raises(ConfigError):
        Settings.from_env(base_dir=tmp_path)


def test_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCORD_TOKEN", "abc")
    s = Settings.from_env(base_dir=tmp_path)
    assert s.commands_file == tmp_path / "data" / "commands.json"
    assert s.audio_dir == tmp_path / "audio_clips"
    assert s.wow_dir is None
    assert not s.sync_on_startup
    assert s.max_download_mb == 10


def test_reads_dotenv_and_overrides(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("DISCORD_TOKEN=do-arquivo\nSYNC_ON_STARTUP=sim\n")
    monkeypatch.setenv("WOW_OST_DIR", str(tmp_path / "ost"))
    monkeypatch.setenv("DEV_GUILD_ID", "123")
    s = Settings.from_env(base_dir=tmp_path)
    assert s.token == "do-arquivo"
    assert s.sync_on_startup
    assert s.wow_dir == tmp_path / "ost"
    assert s.dev_guild_id == 123


def test_legacy_wow_music_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCORD_TOKEN", "abc")
    (tmp_path / "wow-music").mkdir()
    assert Settings.from_env(base_dir=tmp_path).wow_dir == tmp_path / "wow-music"


def test_invalid_int(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCORD_TOKEN", "abc")
    monkeypatch.setenv("MAX_DOWNLOAD_MB", "muito")
    with pytest.raises(ConfigError):
        Settings.from_env(base_dir=tmp_path)
