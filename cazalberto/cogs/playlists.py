"""Comandos para criar e tocar playlists."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from ..errors import UserError
from ..text import chunk_lines, normalize_name
from ._common import filter_choices

if TYPE_CHECKING:
    from ..bot import CazalbertoBot

MAX_REPEAT = 5


class PlaylistCog(commands.Cog, name="Playlists"):
    """💿 Playlists"""

    def __init__(self, bot: CazalbertoBot) -> None:
        self.bot = bot

    async def _playlist_names(self, _: discord.Interaction, current: str):
        return filter_choices(list(self.bot.playlists.all()), current)

    async def _audio_names(self, _: discord.Interaction, current: str):
        return filter_choices(self.bot.library.names() + self.bot.wow.names(), current)

    @app_commands.command(name="criar_playlist", description="Cria uma nova playlist vazia.")
    @app_commands.describe(nome="Nome da playlist")
    async def criar(self, interaction: discord.Interaction, nome: str) -> None:
        name = self.bot.playlists.create(nome)
        await interaction.response.send_message(f"✅ Playlist `{name}` criada!")

    @app_commands.command(
        name="adicionar_playlist", description="Adiciona um áudio a uma playlist."
    )
    @app_commands.describe(playlist="Nome da playlist", audio="Nome do áudio")
    @app_commands.autocomplete(playlist=_playlist_names, audio=_audio_names)
    async def adicionar(self, interaction: discord.Interaction, playlist: str, audio: str) -> None:
        if self.bot.resolve_audio(audio) is None:
            raise UserError(f"❌ O áudio `{normalize_name(audio)}` não existe! Veja `/aprendido`.")
        self.bot.playlists.add(playlist, audio)
        await interaction.response.send_message(
            f"✅ `{normalize_name(audio)}` adicionado à playlist `{normalize_name(playlist)}`!"
        )

    @app_commands.command(name="remover_playlist", description="Remove um áudio de uma playlist.")
    @app_commands.describe(playlist="Nome da playlist", audio="Nome do áudio")
    @app_commands.autocomplete(playlist=_playlist_names)
    async def remover(self, interaction: discord.Interaction, playlist: str, audio: str) -> None:
        self.bot.playlists.remove(playlist, audio)
        await interaction.response.send_message(
            f"✅ `{normalize_name(audio)}` removido da playlist `{normalize_name(playlist)}`!"
        )

    @app_commands.command(name="ver_playlist", description="Mostra os áudios de uma playlist.")
    @app_commands.describe(playlist="Nome da playlist")
    @app_commands.autocomplete(playlist=_playlist_names)
    async def ver(self, interaction: discord.Interaction, playlist: str) -> None:
        items = self.bot.playlists.get(playlist)
        if not items:
            raise UserError(f"📂 A playlist `{normalize_name(playlist)}` está vazia.")
        lines = [f"🎵 Playlist `{normalize_name(playlist)}` ({len(items)} áudios)", ""]
        lines += [f"{i}. {name}" for i, name in enumerate(items, 1)]
        chunks = chunk_lines("\n".join(lines))
        await interaction.response.send_message(chunks[0])
        for chunk in chunks[1:]:
            await interaction.followup.send(chunk)

    @app_commands.command(name="listar_playlists", description="Lista todas as playlists.")
    async def listar(self, interaction: discord.Interaction) -> None:
        playlists = self.bot.playlists.all()
        if not playlists:
            raise UserError("📂 Ainda não há playlists. Use `/criar_playlist`.")
        lines = [f"📋 Playlists ({len(playlists)}):", ""]
        lines += [f"• `{name}`: {len(items)} áudios" for name, items in playlists.items()]
        chunks = chunk_lines("\n".join(lines))
        await interaction.response.send_message(chunks[0])
        for chunk in chunks[1:]:
            await interaction.followup.send(chunk)

    @app_commands.command(name="excluir_playlist", description="Exclui uma playlist.")
    @app_commands.describe(playlist="Nome da playlist")
    @app_commands.autocomplete(playlist=_playlist_names)
    async def excluir(self, interaction: discord.Interaction, playlist: str) -> None:
        self.bot.playlists.delete(playlist)
        await interaction.response.send_message(
            f"🗑️ Playlist `{normalize_name(playlist)}` excluída!"
        )

    @app_commands.command(
        name="tocar_playlist", description="Toca os áudios de uma playlist em sequência."
    )
    @app_commands.describe(
        playlist="Nome da playlist",
        repetir=f"Quantas vezes repetir (1 a {MAX_REPEAT})",
        aleatorio="Tocar em ordem aleatória",
    )
    @app_commands.autocomplete(playlist=_playlist_names)
    async def tocar(
        self,
        interaction: discord.Interaction,
        playlist: str,
        repetir: app_commands.Range[int, 1, MAX_REPEAT] = 1,
        aleatorio: bool = False,
    ) -> None:
        name = normalize_name(playlist)
        items = self.bot.playlists.get(name)
        tracks = [(audio, path) for audio in items if (path := self.bot.resolve_audio(audio))]
        if not tracks:
            raise UserError(f"📂 A playlist `{name}` está vazia ou os áudios não existem mais.")

        vc = await self.bot.player.connect(interaction)
        order = "ordem aleatória" if aleatorio else "em sequência"
        times = f", {repetir}x" if repetir > 1 else ""
        await interaction.response.send_message(f"🎵 Tocando a playlist `{name}` ({order}{times}).")
        channel = interaction.channel

        async def on_track(audio: str) -> None:
            if channel is not None:
                await channel.send(f"▶️ `{audio}` (playlist `{name}`)")

        async def on_finish() -> None:
            if channel is not None:
                await channel.send(f"✅ Playlist `{name}` concluída!")

        self.bot.player.start_queue(
            vc, tracks, repeat=repetir, shuffle=aleatorio, on_track=on_track, on_finish=on_finish
        )


async def setup(bot: CazalbertoBot) -> None:
    await bot.add_cog(PlaylistCog(bot))
