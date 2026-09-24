"""Funções usadas por mais de um cog."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands

from ..errors import UserError
from ..text import normalize_name

if TYPE_CHECKING:
    from ..bot import CazalbertoBot

AUTOCOMPLETE_LIMIT = 25


async def play_by_name(bot: CazalbertoBot, interaction: discord.Interaction, name: str) -> None:
    """Toca um áudio (personalizado ou do WoW) no canal de voz de quem pediu."""
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True, thinking=True)

    path = bot.resolve_audio(name)
    if path is None:
        raise UserError(f"❌ Áudio `{normalize_name(name)}` não encontrado. Tente `/aprendido`.")

    vc = await bot.player.connect(interaction)
    bot.player.cancel_queue(vc.guild.id)
    await bot.player.play(vc, path)
    await interaction.followup.send(f"🎵 Tocando: `{normalize_name(name)}`", ephemeral=True)


def filter_choices(names: list[str], current: str) -> list[app_commands.Choice[str]]:
    """Sugestões do autocomplete: primeiro quem começa com o texto, depois quem contém."""
    current = normalize_name(current)
    starts = [n for n in names if n.startswith(current)]
    contains = [n for n in names if current in n and not n.startswith(current)]
    return [
        app_commands.Choice(name=n[:100], value=n[:100])
        for n in (starts + contains)[:AUTOCOMPLETE_LIMIT]
    ]
