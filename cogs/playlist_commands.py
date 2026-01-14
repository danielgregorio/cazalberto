import discord
import os
import asyncio
import logging
from discord.ext import commands
from discord import app_commands
import random

from config import PLAYLISTS_FILE, COMMANDS_FILE
from utils import load_json, save_json


class PlaylistCommands(commands.Cog):
    """Comandos para gerenciar playlists de áudio."""

    def __init__(self, bot):
        self.bot = bot
        self.custom_commands = load_json(COMMANDS_FILE)
        self.playlists = load_json(PLAYLISTS_FILE)
        # Controle de reprodução de playlist por servidor
        self.playlist_playing: dict = {}

    def _reload_commands(self):
        """Recarrega os comandos do arquivo (para sincronização com audio_commands)."""
        self.custom_commands = load_json(COMMANDS_FILE)

    @app_commands.command(name="criar_playlist", description="Cria uma nova playlist vazia.")
    @app_commands.describe(nome="Nome da playlist a ser criada")
    async def criar_playlist(self, ctx: discord.Interaction, nome: str):
        """Cria uma nova playlist vazia."""
        nome = nome.lower().strip()

        if not nome or len(nome) > 32:
            await ctx.response.send_message("O nome da playlist deve ter entre 1 e 32 caracteres.")
            return

        if nome in self.playlists:
            await ctx.response.send_message(f"A playlist `{nome}` já existe!")
            return

        self.playlists[nome] = []
        save_json(PLAYLISTS_FILE, self.playlists)

        await ctx.response.send_message(f"Playlist `{nome}` criada com sucesso!")

    @app_commands.command(name="adicionar_playlist", description="Adiciona um áudio a uma playlist existente.")
    @app_commands.describe(
        playlist="Nome da playlist onde adicionar o áudio",
        audio="Nome do comando de áudio a ser adicionado"
    )
    async def adicionar_playlist(self, ctx: discord.Interaction, playlist: str, audio: str):
        """Adiciona um áudio a uma playlist existente."""
        playlist = playlist.lower().strip()
        audio = audio.lower().strip()

        if playlist not in self.playlists:
            await ctx.response.send_message(f"A playlist `{playlist}` não existe! Use `/criar_playlist` para criar.")
            return

        # Recarrega comandos para garantir sincronização
        self._reload_commands()

        if audio not in self.custom_commands:
            await ctx.response.send_message(f"O áudio `{audio}` não existe! Use `/aprendido` para ver a lista.")
            return

        if audio in self.playlists[playlist]:
            await ctx.response.send_message(f"O áudio `{audio}` já está na playlist `{playlist}`.")
            return

        self.playlists[playlist].append(audio)
        save_json(PLAYLISTS_FILE, self.playlists)

        await ctx.response.send_message(f"Áudio `{audio}` adicionado à playlist `{playlist}`!")

    @app_commands.command(name="remover_playlist", description="Remove um áudio de uma playlist.")
    @app_commands.describe(
        playlist="Nome da playlist de onde remover o áudio",
        audio="Nome do comando de áudio a ser removido"
    )
    async def remover_playlist(self, ctx: discord.Interaction, playlist: str, audio: str):
        """Remove um áudio de uma playlist."""
        playlist = playlist.lower().strip()
        audio = audio.lower().strip()

        if playlist not in self.playlists:
            await ctx.response.send_message(f"A playlist `{playlist}` não existe!")
            return

        if audio not in self.playlists[playlist]:
            await ctx.response.send_message(f"O áudio `{audio}` não está na playlist `{playlist}`.")
            return

        self.playlists[playlist].remove(audio)
        save_json(PLAYLISTS_FILE, self.playlists)

        await ctx.response.send_message(f"Áudio `{audio}` removido da playlist `{playlist}`!")

    @app_commands.command(name="ver_playlist", description="Mostra os áudios em uma playlist.")
    @app_commands.describe(playlist="Nome da playlist para visualizar")
    async def ver_playlist(self, ctx: discord.Interaction, playlist: str):
        """Mostra os áudios em uma playlist específica."""
        playlist = playlist.lower().strip()

        if playlist not in self.playlists:
            await ctx.response.send_message(f"A playlist `{playlist}` não existe!")
            return

        if not self.playlists[playlist]:
            await ctx.response.send_message(f"A playlist `{playlist}` está vazia.")
            return

        audio_list = "\n".join([f"{i+1}. {audio}" for i, audio in enumerate(self.playlists[playlist])])
        await ctx.response.send_message(f"Playlist: `{playlist}` ({len(self.playlists[playlist])} áudios)\n\n{audio_list}")

    @app_commands.command(name="listar_playlists", description="Lista todas as playlists disponíveis.")
    async def listar_playlists(self, ctx: discord.Interaction):
        """Lista todas as playlists disponíveis."""
        if not self.playlists:
            await ctx.response.send_message("Não há playlists criadas ainda.")
            return

        playlist_info = "\n".join([f"  `{name}`: {len(items)} áudios" for name, items in self.playlists.items()])
        await ctx.response.send_message(f"Playlists disponíveis ({len(self.playlists)}):\n\n{playlist_info}")

    @app_commands.command(name="excluir_playlist", description="Exclui uma playlist existente.")
    @app_commands.describe(playlist="Nome da playlist a ser excluída")
    async def excluir_playlist(self, ctx: discord.Interaction, playlist: str):
        """Exclui uma playlist existente."""
        playlist = playlist.lower().strip()

        if playlist not in self.playlists:
            await ctx.response.send_message(f"A playlist `{playlist}` não existe!")
            return

        del self.playlists[playlist]
        save_json(PLAYLISTS_FILE, self.playlists)

        await ctx.response.send_message(f"Playlist `{playlist}` excluída com sucesso!")

    @app_commands.command(name="tocar_playlist", description="Toca todos os áudios de uma playlist em sequência.")
    @app_commands.describe(
        playlist="Nome da playlist a ser tocada",
        repetir="Número de vezes para repetir a playlist (1-5)",
        aleatorio="Tocar em ordem aleatória"
    )
    async def tocar_playlist(
        self,
        ctx: discord.Interaction,
        playlist: str,
        repetir: int = 1,
        aleatorio: bool = False
    ):
        """Toca todos os áudios de uma playlist em sequência."""
        playlist = playlist.lower().strip()

        repetir = max(1, min(5, repetir))

        if playlist not in self.playlists:
            await ctx.response.send_message(f"A playlist `{playlist}` não existe!")
            return

        if not self.playlists[playlist]:
            await ctx.response.send_message(f"A playlist `{playlist}` está vazia.")
            return

        if not ctx.user.voice:
            await ctx.response.send_message("Você precisa estar em um canal de voz!")
            return

        # Recarrega comandos
        self._reload_commands()

        # Conecta ao canal de voz
        try:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if not vc or not vc.is_connected():
                vc = await ctx.user.voice.channel.connect()
        except discord.errors.ClientException as e:
            await ctx.response.send_message(f"Erro ao conectar ao canal de voz: {e}")
            return

        guild_id = ctx.guild.id
        self.playlist_playing[guild_id] = True

        await ctx.response.send_message(
            f"Tocando playlist `{playlist}` "
            f"({'ordem aleatória' if aleatorio else 'sequencial'})"
            f"{f', {repetir} vezes' if repetir > 1 else ''}"
        )

        async def play_playlist_items():
            audios_to_play = self.playlists[playlist].copy()

            for rep in range(repetir):
                if not self.playlist_playing.get(guild_id, False):
                    break

                if aleatorio:
                    random.shuffle(audios_to_play)

                for audio in audios_to_play:
                    if not self.playlist_playing.get(guild_id, False):
                        break

                    if audio in self.custom_commands:
                        audio_path = self.custom_commands[audio]

                        if not os.path.exists(audio_path):
                            logging.warning(f"Arquivo não encontrado: {audio_path}")
                            continue

                        if not vc.is_connected():
                            return

                        if vc.is_playing():
                            vc.stop()

                        try:
                            source = discord.FFmpegPCMAudio(audio_path)
                            source = discord.PCMVolumeTransformer(source, volume=1.0)
                            vc.play(source)

                            await ctx.followup.send(f"Tocando: `{audio}` da playlist `{playlist}`")
                        except discord.errors.ClientException as e:
                            logging.error(f"Erro ao tocar {audio}: {e}")
                            continue

                        await asyncio.sleep(1)

                        while vc.is_playing() and self.playlist_playing.get(guild_id, False):
                            await asyncio.sleep(0.5)

                        await asyncio.sleep(0.5)

            self.playlist_playing[guild_id] = False

            try:
                await ctx.followup.send(f"Reprodução da playlist `{playlist}` concluída!")
            except discord.errors.HTTPException:
                pass

        asyncio.create_task(play_playlist_items())

    @app_commands.command(name="parar_playlist", description="Para a reprodução da playlist atual.")
    async def parar_playlist(self, ctx: discord.Interaction):
        """Para a reprodução da playlist atual."""
        guild_id = ctx.guild.id

        if guild_id in self.playlist_playing and self.playlist_playing[guild_id]:
            self.playlist_playing[guild_id] = False

            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc and vc.is_playing():
                vc.stop()

            await ctx.response.send_message("Reprodução da playlist parada!")
        else:
            await ctx.response.send_message("Nenhuma playlist está sendo reproduzida.")


async def setup(bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(PlaylistCommands(bot))
