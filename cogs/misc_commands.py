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
    
    @commands.command(name="sync")
    async def sync_command(self, ctx):
        """Sincroniza os comandos slash com o Discord (comando de prefixo)."""
        if ctx.author.guild_permissions.administrator:  # Apenas administradores podem usar
            try:
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
