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
    
    @app_commands.command(name="criar_playlist", description="Cria uma nova playlist vazia.")
    @app_commands.describe(nome="Nome da playlist a ser criada")
    async def criar_playlist(self, ctx: discord.Interaction, nome: str):
        """Cria uma nova playlist vazia."""
        nome = nome.lower().strip()
        
        # Verifica se o nome é válido
        if not nome or len(nome) > 32:
            await ctx.response.send_message("❌ O nome da playlist deve ter entre 1 e 32 caracteres.")
            return
        
        # Verifica se a playlist já existe
        if nome in self.playlists:
            await ctx.response.send_message(f"❌ A playlist `{nome}` já existe!")
            return
        
        # Cria a nova playlist vazia
        self.playlists[nome] = []
        save_json(PLAYLISTS_FILE, self.playlists)
        
        await ctx.response.send_message(f"✅ Playlist `{nome}` criada com sucesso!")
    
    @app_commands.command(name="adicionar_playlist", description="Adiciona um áudio a uma playlist existente.")
    @app_commands.describe(
        playlist="Nome da playlist onde adicionar o áudio",
        audio="Nome do comando de áudio a ser adicionado"
    )
    async def adicionar_playlist(self, ctx: discord.Interaction, playlist: str, audio: str):
        """Adiciona um áudio a uma playlist existente."""
        playlist = playlist.lower().strip()
        audio = audio.lower().strip()
        
        # Verifica se a playlist existe
        if playlist not in self.playlists:
            await ctx.response.send_message(f"❌ A playlist `{playlist}` não existe! Use `/criar_playlist` para criar.")
            return
        
        # Verifica se o áudio existe
        if audio not in self.custom_commands:
            await ctx.response.send_message(f"❌ O áudio `{audio}` não existe! Use `/aprendido` para ver a lista de áudios.")
            return
        
        # Verifica se o áudio já está na playlist
        if audio in self.playlists[playlist]:
            await ctx.response.send_message(f"❌ O áudio `{audio}` já está na playlist `{playlist}`.")
            return
        
        # Adiciona o áudio à playlist
        self.playlists[playlist].append(audio)
        save_json(PLAYLISTS_FILE, self.playlists)
        
        await ctx.response.send_message(f"✅ Áudio `{audio}` adicionado à playlist `{playlist}`!")
    
    @app_commands.command(name="remover_playlist", description="Remove um áudio de uma playlist.")
    @app_commands.describe(
        playlist="Nome da playlist de onde remover o áudio",
        audio="Nome do comando de áudio a ser removido"
    )
    async def remover_playlist(self, ctx: discord.Interaction, playlist: str, audio: str):
        """Remove um áudio de uma playlist."""
        playlist = playlist.lower().strip()
        audio = audio.lower().strip()
        
        # Verifica se a playlist existe
        if playlist not in self.playlists:
            await ctx.response.send_message(f"❌ A playlist `{playlist}` não existe!")
            return
        
        # Verifica se o áudio está na playlist
        if audio not in self.playlists[playlist]:
            await ctx.response.send_message(f"❌ O áudio `{audio}` não está na playlist `{playlist}`.")
            return
        
        # Remove o áudio da playlist
        self.playlists[playlist].remove(audio)
        save_json(PLAYLISTS_FILE, self.playlists)
        
        await ctx.response.send_message(f"✅ Áudio `{audio}` removido da playlist `{playlist}`!")
    
    @app_commands.command(name="ver_playlist", description="Mostra os áudios em uma playlist.")
    @app_commands.describe(playlist="Nome da playlist para visualizar")
    async def ver_playlist(self, ctx: discord.Interaction, playlist: str):
        """Mostra os áudios em uma playlist específica."""
        playlist = playlist.lower().strip()
        
        # Verifica se a playlist existe
        if playlist not in self.playlists:
            await ctx.response.send_message(f"❌ A playlist `{playlist}` não existe!")
            return
        
        # Verifica se a playlist está vazia
        if not self.playlists[playlist]:
            await ctx.response.send_message(f"📂 A playlist `{playlist}` está vazia.")
            return
        
        # Lista os áudios da playlist
        audio_list = "\n".join([f"{i+1}. {audio}" for i, audio in enumerate(self.playlists[playlist])])
        await ctx.response.send_message(f"🎵 Playlist: `{playlist}` ({len(self.playlists[playlist])} áudios)\n\n{audio_list}")
    
    @app_commands.command(name="listar_playlists", description="Lista todas as playlists disponíveis.")
    async def listar_playlists(self, ctx: discord.Interaction):
        """Lista todas as playlists disponíveis."""
        # Verifica se existem playlists
        if not self.playlists:
            await ctx.response.send_message("📂 Não há playlists criadas ainda.")
            return
        
        # Lista todas as playlists e seus tamanhos
        playlist_info = "\n".join([f"• `{name}`: {len(items)} áudios" for name, items in self.playlists.items()])
        await ctx.response.send_message(f"📋 Playlists disponíveis ({len(self.playlists)}):\n\n{playlist_info}")
    
    @app_commands.command(name="excluir_playlist", description="Exclui uma playlist existente.")
    @app_commands.describe(playlist="Nome da playlist a ser excluída")
    async def excluir_playlist(self, ctx: discord.Interaction, playlist: str):
        """Exclui uma playlist existente."""
        playlist = playlist.lower().strip()
        
        # Verifica se a playlist existe
        if playlist not in self.playlists:
            await ctx.response.send_message(f"❌ A playlist `{playlist}` não existe!")
            return
        
        # Remove a playlist
        del self.playlists[playlist]
        save_json(PLAYLISTS_FILE, self.playlists)
        
        await ctx.response.send_message(f"🗑️ Playlist `{playlist}` excluída com sucesso!")
    
    @app_commands.command(name="tocar_playlist", description="Toca todos os áudios de uma playlist em sequência.")
    @app_commands.describe(
        playlist="Nome da playlist a ser tocada",
        repetir="Número de vezes para repetir a playlist (opcional)",
        aleatorio="Tocar em ordem aleatória (opcional)"
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
        
        # Limita o número de repetições para evitar spam
        repetir = max(1, min(5, repetir))
        
        # Verifica se a playlist existe
        if playlist not in self.playlists:
            await ctx.response.send_message(f"❌ A playlist `{playlist}` não existe!")
            return
        
        # Verifica se a playlist está vazia
        if not self.playlists[playlist]:
            await ctx.response.send_message(f"📂 A playlist `{playlist}` está vazia.")
            return
        
        # Verifica se o usuário está em um canal de voz
        if not ctx.user.voice:
            await ctx.response.send_message("❌ Você precisa estar em um canal de voz!")
            return
        
        # Conecta ao canal de voz
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not vc or not vc.is_connected():
            vc = await ctx.user.voice.channel.connect()
        
        # Responde inicialmente
        await ctx.response.send_message(
            f"🎵 Tocando playlist `{playlist}` "
            f"({'ordem aleatória' if aleatorio else 'sequencial'})"
            f"{f', {repetir} vezes' if repetir > 1 else ''}"
        )
        
        # Função para reproduzir a playlist
        async def play_playlist_items():
            # Lista de áudios a serem tocados
            audios_to_play = self.playlists[playlist].copy()
            
            for _ in range(repetir):
                # Embaralha se for aleatório
                if aleatorio:
                    random.shuffle(audios_to_play)
                
                for audio in audios_to_play:
                    # Verifica se o áudio ainda existe
                    if audio in self.custom_commands:
                        audio_path = self.custom_commands[audio]
                        
                        # Verifica se ainda está conectado
                        if not vc.is_connected():
                            return
                        
                        # Para qualquer áudio atual e toca o próximo
                        if vc.is_playing():
                            vc.stop()
                        
                        # Toca o áudio e aguarda
                        vc.play(discord.FFmpegPCMAudio(audio_path))
                        
                        # Envia mensagem informando o áudio atual
                        try:
                            await ctx.followup.send(f"🎵 Tocando: `{audio}` da playlist `{playlist}`")
                        except:
                            pass  # Ignora erros de mensagem
                        
                        # Pequena pausa antes de verificar se o áudio ainda está tocando
                        await asyncio.sleep(1)
                        
                        # Espera até que o áudio termine
                        while vc.is_playing():
                            await asyncio.sleep(0.5)
                        
                        # Pequena pausa entre áudios
                        await asyncio.sleep(1)
            
            # Envia mensagem quando terminar
            try:
                await ctx.followup.send(f"✅ Reprodução da playlist `{playlist}` concluída!")
            except:
                pass  # Ignora erros de mensagem
        
        # Inicia a reprodução em segundo plano
        asyncio.create_task(play_playlist_items())

async def setup(bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(PlaylistCommands(bot))
