"""Garante que o bot monta e registra todos os comandos, sem conectar ao Discord."""

from cazalberto.bot import EXTENSIONS, CazalbertoBot
from cazalberto.config import Settings


def make_settings(tmp_path):
    return Settings(
        token="x",
        command_prefix="!",
        data_dir=tmp_path / "data",
        audio_dir=tmp_path / "audio",
        wow_dir=None,
        sync_on_startup=False,
        dev_guild_id=None,
        log_level="INFO",
        log_file=None,
        max_download_mb=1,
    )


async def test_all_extensions_load(tmp_path):
    bot = CazalbertoBot(make_settings(tmp_path))
    async with bot:
        for extension in EXTENSIONS:
            await bot.load_extension(extension)
        names = {c.name for c in bot.tree.get_commands()}
        assert {"tocar", "aprender", "esquecer", "wow", "tocar_playlist", "ajuda"} <= names
        assert bot.get_command("sync") is not None
        # Limites do Discord: nome até 32 e descrição até 100 caracteres.
        for command in bot.tree.walk_commands():
            assert len(command.name) <= 32
            assert 1 <= len(command.description) <= 100
