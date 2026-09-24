"""Comandos das trilhas sonoras de World of Warcraft."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from ..audio.wow import EXPANSIONS
from ..errors import UserError
from ..ui.browser import AudioBrowser
from ._common import play_by_name

if TYPE_CHECKING:
    from ..bot import CazalbertoBot


def _expansion_help() -> str:
    lines = [f"• `{e.key}` ({e.aliases[0]}): {e.title}" for e in EXPANSIONS]
    return "Expansões disponíveis:\n" + "\n".join(lines)


class WowCog(commands.Cog, name="World of Warcraft"):
    """🐉 Trilhas sonoras do WoW"""

    def __init__(self, bot: CazalbertoBot) -> None:
        self.bot = bot

    async def _expansions(self, _: discord.Interaction, current: str):
        current = current.lower()
        return [
            app_commands.Choice(name=e.title, value=e.key)
            for e in EXPANSIONS
            if current in e.key or current in e.title.lower()
        ][:25]

    @app_commands.command(name="wow", description="Lista as músicas de uma expansão do WoW.")
    @app_commands.describe(expansao="Expansão (ex.: classic, wotlk, 2) ou patch (ex.: kara)")
    @app_commands.autocomplete(expansao=_expansions)
    async def wow(self, interaction: discord.Interaction, expansao: str) -> None:
        catalog = self.bot.wow
        if not catalog.enabled:
            raise UserError(
                "❌ As trilhas do WoW estão desativadas. Configure `WOW_OST_DIR` no `.env`."
            )

        result = catalog.list(expansao)
        if result is None:
            raise UserError(f"❌ Expansão `{expansao}` não reconhecida.\n\n{_expansion_help()}")
        title, names = result
        if not names:
            raise UserError(f"❌ Nenhuma música encontrada para {title}.")

        view = AudioBrowser(
            names, lambda i, name: play_by_name(self.bot, i, name), strip_prefix=True
        )
        await interaction.response.send_message(
            f"🎵 {title}: {len(names)} músicas. Clique para tocar (ou use `/tocar {names[0]}`):",
            view=view,
        )
        view.message = await interaction.original_response()


async def setup(bot: CazalbertoBot) -> None:
    await bot.add_cog(WowCog(bot))
