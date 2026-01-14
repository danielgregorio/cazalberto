import discord
from discord.ext import commands
from discord import app_commands
import random
import logging

from config import JOKES_FILE, VERSION
from utils import load_json


class MiscCommands(commands.Cog):
    """Comandos diversos do Cazalberto."""

    def __init__(self, bot):
        self.bot = bot
        self.jokes = load_json(JOKES_FILE)

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
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice_status = "Conectado" if vc and vc.is_connected() else "Desconectado"
        playing_status = "Tocando áudio" if vc and vc.is_playing() else "Parado"

        latency = round(self.bot.latency * 1000)
        uptime = discord.utils.utcnow() - self.bot.user.created_at
        uptime_str = f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds // 60) % 60}m"

        commands_count = len(self.bot.tree.get_commands())
        channel_name = vc.channel.name if vc and vc.is_connected() else "Nenhum"

        embed = discord.Embed(
            title="Status do Cazalberto",
            description=f"Versão {VERSION}",
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
            description=f"Versão {VERSION} - Aqui estão os comandos disponíveis:",
            color=0x3498db
        )

        # Comandos de reprodução
        embed.add_field(
            name="Reprodução",
            value=(
                "`/tocar [comando]` - Toca um áudio\n"
                "`/fila [comando]` - Adiciona à fila\n"
                "`/ver_fila` - Mostra a fila atual\n"
                "`/limpar_fila` - Limpa a fila\n"
                "`/pausar` - Pausa a reprodução\n"
                "`/continuar` - Continua a reprodução\n"
                "`/pular` - Pula para o próximo\n"
                "`/volume [0-200]` - Ajusta o volume\n"
                "`/loop` - Ativa/desativa loop\n"
                "`/sair` - Sai do canal de voz"
            ),
            inline=False
        )

        # Comandos de gerenciamento de áudio
        embed.add_field(
            name="Gerenciamento de Áudio",
            value=(
                "`/aprender [comando] [url]` - Adiciona novo áudio\n"
                "`/esquecer [comando]` - Remove um áudio\n"
                "`/aprendido` - Lista todos os áudios\n"
                "`/buscar [termo]` - Busca áudios por nome\n"
                "`/wow [expansão]` - Lista áudios do WoW"
            ),
            inline=False
        )

        # Comandos de favoritos
        embed.add_field(
            name="Favoritos",
            value=(
                "`/favoritar [comando]` - Favorita um áudio\n"
                "`/desfavoritar [comando]` - Remove dos favoritos\n"
                "`/favoritos` - Mostra seus favoritos"
            ),
            inline=False
        )

        # Comandos de playlist
        embed.add_field(
            name="Playlists",
            value=(
                "`/criar_playlist [nome]` - Cria playlist\n"
                "`/adicionar_playlist [playlist] [audio]` - Adiciona áudio\n"
                "`/remover_playlist [playlist] [audio]` - Remove áudio\n"
                "`/ver_playlist [playlist]` - Mostra conteúdo\n"
                "`/listar_playlists` - Lista playlists\n"
                "`/excluir_playlist [playlist]` - Exclui playlist\n"
                "`/tocar_playlist [playlist]` - Toca playlist\n"
                "`/parar_playlist` - Para playlist"
            ),
            inline=False
        )

        # Comandos diversos
        embed.add_field(
            name="Outros",
            value=(
                "`/ranking [qtd]` - Ranking dos mais tocados\n"
                "`/piada` - Conta uma piada\n"
                "`/status` - Status do bot"
            ),
            inline=False
        )

        # Dicas
        embed.add_field(
            name="Dicas",
            value=(
                "  Para WoW: `/tocar wotlk-dalaran` ou `/wow classic`\n"
                "  Expansões: 0-11 ou classic, tbc, wotlk, cata, mop, wod, legion, bfa, sl, df, tww, undermine"
            ),
            inline=False
        )

        embed.set_footer(text=f"Desenvolvido por Daniel Gregorio | v{VERSION}")

        await ctx.response.send_message(embed=embed)

    @commands.command(name="sync")
    async def sync_command(self, ctx):
        """Sincroniza os comandos slash com o Discord (comando de prefixo)."""
        if ctx.author.guild_permissions.administrator:
            try:
                await ctx.send("Iniciando sincronização...")

                synced_global = await self.bot.tree.sync()
                await ctx.send(f"Sincronizados {len(synced_global)} comandos globalmente!")

                synced = await self.bot.tree.sync(guild=ctx.guild)
                await ctx.send(f"Sincronizados {len(synced)} comandos com este servidor!")

                command_list = "\n".join([f"  /{command.name}" for command in synced])
                if command_list:
                    await ctx.send(f"Comandos disponíveis:\n{command_list}")
            except discord.errors.HTTPException as e:
                await ctx.send(f"Erro HTTP durante a sincronização: {e}")
            except Exception as e:
                logging.error(f"Erro na sincronização: {type(e).__name__}: {e}")
                await ctx.send(f"Erro durante a sincronização: {e}")
        else:
            await ctx.send("Você precisa ser administrador para usar este comando!")


async def setup(bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(MiscCommands(bot))
