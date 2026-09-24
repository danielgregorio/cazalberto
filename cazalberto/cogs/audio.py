"""Comandos para tocar e gerenciar os áudios personalizados."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from ..audio.download import download_audio
from ..errors import UserError
from ..ui.browser import AudioBrowser
from ._common import filter_choices, play_by_name

if TYPE_CHECKING:
    from ..bot import CazalbertoBot

log = logging.getLogger(__name__)


class AudioCog(commands.Cog, name="Áudio"):
    """🎵 Tocar e gerenciar áudios"""

    def __init__(self, bot: CazalbertoBot) -> None:
        self.bot = bot

    async def _all_audio(self, _: discord.Interaction, current: str):
        return filter_choices(self.bot.library.names() + list(self.bot.wow.names()), current)

    async def _custom_audio(self, _: discord.Interaction, current: str):
        return filter_choices(self.bot.library.names(), current)

    @app_commands.command(name="tocar", description="Toca um áudio salvo (ou uma música do WoW).")
    @app_commands.describe(comando="Nome do áudio, ex.: quico ou classic-stormwind")
    @app_commands.autocomplete(comando=_all_audio)
    async def tocar(self, interaction: discord.Interaction, comando: str) -> None:
        await play_by_name(self.bot, interaction, comando)

    @app_commands.command(
        name="aprendido", description="Lista os áudios aprendidos, com botões para tocar."
    )
    async def aprendido(self, interaction: discord.Interaction) -> None:
        names = self.bot.library.names()
        if not names:
            raise UserError("❌ Nenhum áudio foi aprendido ainda. Use `/aprender`.")

        view = AudioBrowser(names, lambda i, name: play_by_name(self.bot, i, name))
        text = f"🎵 {len(names)} áudios disponíveis. Clique para tocar:"
        if self.bot.wow.enabled:
            text += "\nℹ️ Para as trilhas do World of Warcraft, use `/wow <expansão>`."
        await interaction.response.send_message(text, view=view)
        view.message = await interaction.original_response()

    @app_commands.command(name="aprender", description="Ensina um novo áudio a partir de uma URL.")
    @app_commands.describe(comando="Nome do novo áudio", url="Link direto para o arquivo de áudio")
    async def aprender(self, interaction: discord.Interaction, comando: str, url: str) -> None:
        library = self.bot.library
        name = library.validate_name(comando)
        if name in library:
            raise UserError(f"❌ O comando `{name}` já existe!")

        await interaction.response.defer(thinking=True)
        destination = library.target_path(name)
        assert self.bot.http_session is not None
        await download_audio(
            self.bot.http_session,
            url,
            destination,
            max_bytes=self.bot.settings.max_download_mb * 1024 * 1024,
        )
        try:
            library.add(name, destination)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        log.info("%s ensinou o áudio %r", interaction.user, name)
        await interaction.followup.send(f"✅ Aprendi `{name}`! Use `/tocar {name}` para ouvir.")

    @app_commands.command(name="esquecer", description="Remove um áudio aprendido.")
    @app_commands.describe(comando="Nome do áudio a remover")
    @app_commands.autocomplete(comando=_custom_audio)
    async def esquecer(self, interaction: discord.Interaction, comando: str) -> None:
        file = self.bot.library.remove(comando)
        self.bot.playlists.remove_everywhere(comando)
        deleted = False
        if file is not None:
            try:
                file.unlink(missing_ok=True)
                deleted = True
            except OSError as exc:
                log.warning("Não consegui apagar %s: %s", file, exc)
        log.info("%s removeu o áudio %r", interaction.user, comando)
        suffix = " e o arquivo foi apagado" if deleted else ""
        await interaction.response.send_message(f"✅ Esqueci `{comando}`{suffix}.")

    @app_commands.command(name="parar", description="Para o áudio ou a playlist que está tocando.")
    async def parar(self, interaction: discord.Interaction) -> None:
        vc = self.bot.player.voice_client(interaction.guild)
        if vc is None:
            raise UserError("❌ Não estou tocando nada.")
        self.bot.player.cancel_queue(vc.guild.id)
        vc.stop()
        await interaction.response.send_message("⏹️ Parei.")

    @app_commands.command(name="sair", description="Faz o bot sair do canal de voz.")
    async def sair(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None or not await self.bot.player.stop(interaction.guild):
            raise UserError("❌ Não estou conectado a nenhum canal de voz!")
        await interaction.response.send_message("👋 Saí do canal de voz!")


async def setup(bot: CazalbertoBot) -> None:
    await bot.add_cog(AudioCog(bot))
