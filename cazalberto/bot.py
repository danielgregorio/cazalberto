"""Classe principal do bot: junta configuração, serviços e cogs."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from . import __version__
from .audio.library import AudioLibrary
from .audio.player import VoicePlayer
from .audio.wow import WowCatalog
from .config import PROJECT_ROOT, Settings
from .errors import UserError
from .playlists import PlaylistStore

log = logging.getLogger(__name__)

EXTENSIONS = (
    "cazalberto.cogs.audio",
    "cazalberto.cogs.wow",
    "cazalberto.cogs.playlists",
    "cazalberto.cogs.misc",
    "cazalberto.cogs.admin",
)


def _adopt_legacy_file(legacy: Path, current: Path) -> None:
    """Versões antigas guardavam os dados na raiz do projeto. Se o arquivo novo
    ainda não existe, copia o antigo (o original fica intacto)."""
    if legacy.is_file() and not current.exists():
        shutil.copy2(legacy, current)
        log.info("Copiado %s para %s (formato antigo).", legacy, current)


class CazalbertoBot(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True  # necessário para os comandos com prefixo (!sync)
        intents.voice_states = True
        super().__init__(command_prefix=settings.command_prefix, intents=intents)

        self.settings = settings
        self.version = __version__
        self.library = AudioLibrary(settings.commands_file, settings.audio_dir)
        self.playlists = PlaylistStore(settings.playlists_file)
        self.wow = WowCatalog(settings.wow_dir)
        self.player = VoicePlayer(self)
        self.http_session: aiohttp.ClientSession | None = None
        self.started_at = discord.utils.utcnow()

        self.tree.on_error = self.on_app_command_error

    async def setup_hook(self) -> None:
        self.settings.audio_dir.mkdir(parents=True, exist_ok=True)
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        _adopt_legacy_file(PROJECT_ROOT / "playlists.json", self.settings.playlists_file)
        self.library.load()
        self.playlists.load()
        self.wow.scan()
        self.http_session = aiohttp.ClientSession()

        for extension in EXTENSIONS:
            await self.load_extension(extension)
            log.info("Extensão carregada: %s", extension)

        if self.settings.sync_on_startup:
            await self.sync_commands()

    async def sync_commands(self) -> list[app_commands.AppCommand]:
        """Registra os comandos slash no Discord. Com DEV_GUILD_ID, sincroniza só
        naquele servidor (aparece na hora, útil para testes)."""
        if self.settings.dev_guild_id:
            guild = discord.Object(id=self.settings.dev_guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
        else:
            synced = await self.tree.sync()
        log.info("%d comandos slash sincronizados.", len(synced))
        return synced

    async def close(self) -> None:
        if self.http_session is not None:
            await self.http_session.close()
        await super().close()

    async def on_ready(self) -> None:
        log.info("Conectado como %s (ID %s)", self.user, self.user.id if self.user else "?")

    def resolve_audio(self, name: str) -> Path | None:
        """Procura um áudio primeiro nos personalizados e depois nas trilhas do WoW."""
        return self.library.resolve(name) or self.wow.resolve(name)

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        await self.report_error(interaction, getattr(error, "original", error))

    async def report_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """Responde ao usuário com uma mensagem amigável. Erros inesperados vão para o log."""
        if isinstance(error, UserError):
            message = str(error)
        elif isinstance(error, app_commands.CheckFailure):
            message = "❌ Você não tem permissão para usar esse comando."
        else:
            command = interaction.command.qualified_name if interaction.command else "componente"
            log.error("Erro em %s", command, exc_info=error)
            message = "❌ Ocorreu um erro inesperado. Veja o log do bot para detalhes."

        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except discord.HTTPException:
            log.warning("Não foi possível enviar a mensagem de erro ao usuário.")
