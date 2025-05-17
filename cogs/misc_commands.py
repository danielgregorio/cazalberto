import discord
from discord.ext import commands
from discord import app_commands
import random
import logging

from config import JOKES_FILE
from utils import load_json

class MiscCommands(commands.Cog):
    """Comandos diversos do Cazalberto."""
    
    def __init__(self, bot):
        self.bot = bot
        self.jokes = load_json(JOKES_FILE)
        
        # Se não houver piadas carregadas, usar uma lista padrão
        if not self.jokes:
            self.jokes = [
                "Por que o livro de matemática se suicidou? Porque tinha muitos problemas!",
                "O que um pato disse para o outro? Estamos empatados!",
                "Por que a vaca foi para o espaço? Para ver a Via Láctea!",
                "O que o zero disse para o oito? Belo cinto!",
                "Por que o esqueleto não brigou com ninguém? Porque ele não tem estômago para isso!"
            ]
    
    @app_commands.command(name="piada", description="Conta uma piada aleatória.")
    async def tell_joke(self, ctx: discord.Interaction):
        """Conta uma piada aleatória."""
        joke = random.choice(self.jokes)
        await ctx.response.send_message(joke)
        
    @app_commands.command(name="status", description="Mostra informações sobre o estado do bot.")
    async def status(self, ctx: discord.Interaction):
        """Mostra informações sobre o estado do bot."""
        # Checa conexão de voz
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice_status = "✅ Conectado" if vc and vc.is_connected() else "❌ Desconectado"
        playing_status = "✅ Tocando áudio" if vc and vc.is_playing() else "❌ Não está tocando"
        
        # Informações gerais do bot
        latency = round(self.bot.latency * 1000)  # Converte para ms
        uptime = discord.utils.utcnow() - self.bot.user.created_at
        uptime_str = f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds // 60) % 60}m"
        
        # Comandos disponíveis
        commands_count = len(self.bot.tree.get_commands())
        
        # Status do canal de voz
        channel_name = vc.channel.name if vc and vc.is_connected() else "Nenhum"
        
        # Formata a mensagem
        embed = discord.Embed(
            title="Status do Cazalberto",
            description="Informações sobre o estado atual do bot",
            color=0x00ff00 if vc and vc.is_connected() else 0xff0000
        )
        
        embed.add_field(name="Status de Voz", value=voice_status, inline=True)
        embed.add_field(name="Status de Áudio", value=playing_status, inline=True)
        embed.add_field(name="Canal Atual", value=channel_name, inline=True)
        
        embed.add_field(name="Latência", value=f"{latency}ms", inline=True)
        embed.add_field(name="Tempo Online", value=uptime_str, inline=True)
        embed.add_field(name="Comandos", value=str(commands_count), inline=True)
        
        embed.set_footer(text="Use /ajuda para ver todos os comandos disponíveis")
        
        await ctx.response.send_message(embed=embed)
        
    @app_commands.command(name="ajuda", description="Mostra informações de ajuda sobre os comandos disponíveis.")
    async def help_command(self, ctx: discord.Interaction):
        """Mostra informações de ajuda sobre os comandos disponíveis."""
        embed = discord.Embed(
            title="Comandos do Cazalberto",
            description="Aqui estão os comandos disponíveis do bot:",
            color=0x3498db
        )
        
        # Comandos de áudio
        embed.add_field(
            name="🎵 Comandos de Áudio",
            value=(
                "`/tocar [comando]` - Toca um áudio salvo\n"
                "`/aprender [comando] [url]` - Adiciona um novo áudio\n"
                "`/aprendido` - Lista todos os áudios salvos\n"
                "`/esquecer [comando]` - Remove um áudio\n"
                "`/aprendido_wow [expansão]` - Lista áudios de uma expansão do WoW"
            ),
            inline=False
        )
        
        # Comandos de playlist
        embed.add_field(
            name="💿 Comandos de Playlist",
            value=(
                "`/criar_playlist [nome]` - Cria uma nova playlist\n"
                "`/adicionar_playlist [playlist] [audio]` - Adiciona áudio à playlist\n"
                "`/remover_playlist [playlist] [audio]` - Remove áudio da playlist\n"
                "`/ver_playlist [playlist]` - Mostra os áudios de uma playlist\n"
                "`/listar_playlists` - Lista todas as playlists\n"
                "`/excluir_playlist [playlist]` - Exclui uma playlist\n"
                "`/tocar_playlist [playlist] [repetir] [aleatorio]` - Toca uma playlist"
            ),
            inline=False
        )
        
        # Comandos diversos
        embed.add_field(
            name="💻 Outros Comandos",
            value=(
                "`/piada` - Conta uma piada aleatória\n"
                "`/status` - Mostra informações sobre o estado do bot\n"
                "`/sair` - Faz o bot sair do canal de voz"
            ),
            inline=False
        )
        
        # Dicas de uso
        embed.add_field(
            name="💡 Dicas",
            value=(
                "• Para tocar músicas do WoW, use `/tocar [expansão]-[música]`\n"
                "• Exemplos: `/tocar wotlk-dalaran` ou `/tocar classic-elwynn`\n"
                "• Os áudios personalizados podem ser tocados diretamente: `/tocar nome`"
            ),
            inline=False
        )
        
        # Rodapé com informações do desenvolvedor
        embed.set_footer(text="Desenvolvido por Daniel Gregorio | v1.0.0")
        
        await ctx.response.send_message(embed=embed)
    
    @commands.command(name="sync")
    async def sync_command(self, ctx):
        """Sincroniza os comandos slash com o Discord (comando de prefixo)."""
        if ctx.author.guild_permissions.administrator:  # Apenas administradores podem usar
            try:
                await ctx.send("🔄 Iniciando sincronização...")
                
                # Sincroniza globalmente (para todos os servidores)
                synced_global = await self.bot.tree.sync()
                await ctx.send(f"🌐 Sincronizados {len(synced_global)} comandos globalmente!")
                
                # Sincroniza com o servidor atual
                synced = await self.bot.tree.sync(guild=ctx.guild)
                await ctx.send(f"✅ Sincronizados {len(synced)} comandos com este servidor!")
                
                # Mostra os comandos sincronizados
                command_list = "\n".join([f"• /{command.name}" for command in synced])
                if command_list:
                    await ctx.send(f"Comandos disponíveis:\n{command_list}")
            except Exception as e:
                await ctx.send(f"❌ Erro durante a sincronização: {e}")
        else:
            await ctx.send("❌ Você precisa ser administrador para usar este comando!")

async def setup(bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(MiscCommands(bot))
