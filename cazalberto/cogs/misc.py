"""Comandos diversos: piada, status e ajuda."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from ..storage import load_json

if TYPE_CHECKING:
    from ..bot import CazalbertoBot

log = logging.getLogger(__name__)

DEFAULT_JOKES = [
    "O que um pato disse para o outro? Estamos empatados!",
    "Por que a vaca foi para o espaço? Para ver a Via Láctea!",
    "O que o zero disse para o oito? Belo cinto!",
    "Por que o esqueleto não brigou com ninguém? Porque ele não tem estômago para isso!",
    "Por que o livro de matemática estava triste? Porque tinha muitos problemas!",
]


def _format_uptime(seconds: int) -> str:
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    return f"{days}d {hours}h {minutes}m"


class MiscCog(commands.Cog, name="Outros"):
    """💻 Outros comandos"""

    def __init__(self, bot: CazalbertoBot) -> None:
        self.bot = bot
        jokes = load_json(bot.settings.jokes_file, [])
        if not (isinstance(jokes, list) and all(isinstance(j, str) for j in jokes) and jokes):
            jokes = DEFAULT_JOKES
        self.jokes: list[str] = jokes

    @app_commands.command(name="piada", description="Conta uma piada aleatória.")
    async def piada(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(random.choice(self.jokes))

    @app_commands.command(name="status", description="Mostra o estado do bot.")
    async def status(self, interaction: discord.Interaction) -> None:
        vc = self.bot.player.voice_client(interaction.guild)
        uptime = int((discord.utils.utcnow() - self.bot.started_at).total_seconds())

        embed = discord.Embed(
            title="Status do Cazalberto",
            color=discord.Color.green() if vc else discord.Color.red(),
        )
        embed.add_field(name="Voz", value=f"✅ {vc.channel.name}" if vc else "❌ Desconectado")
        embed.add_field(name="Tocando", value="✅ Sim" if vc and vc.is_playing() else "❌ Não")
        embed.add_field(name="Latência", value=f"{round(self.bot.latency * 1000)} ms")
        embed.add_field(name="Online há", value=_format_uptime(uptime))
        embed.add_field(name="Áudios", value=str(len(self.bot.library)))
        embed.add_field(
            name="Trilhas WoW",
            value=str(len(self.bot.wow)) if self.bot.wow.enabled else "desativado",
        )
        embed.set_footer(text=f"v{self.bot.version} • /ajuda para ver os comandos")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ajuda", description="Mostra os comandos disponíveis.")
    async def ajuda(self, interaction: discord.Interaction) -> None:
        # Gerado a partir dos comandos registrados, então nunca fica desatualizado.
        embed = discord.Embed(title="Comandos do Cazalberto", color=discord.Color.blurple())
        for cog in self.bot.cogs.values():
            app_cmds = cog.get_app_commands()
            if not app_cmds:
                continue
            lines = [f"`/{c.name}` — {c.description}" for c in app_cmds]
            embed.add_field(
                name=cog.description or cog.qualified_name, value="\n".join(lines), inline=False
            )
        embed.add_field(
            name="💡 Dicas",
            value=(
                "• Músicas do WoW: `/tocar <expansão>-<música>`, ex.: `/tocar classic-elwynn`\n"
                "• Os campos têm autocompletar: comece a digitar e escolha da lista."
            ),
            inline=False,
        )
        embed.set_footer(text=f"Desenvolvido por Daniel Gregorio • v{self.bot.version}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: CazalbertoBot) -> None:
    await bot.add_cog(MiscCog(bot))
