"""Comandos de administração (com prefixo, ex.: !sync)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from ..bot import CazalbertoBot

log = logging.getLogger(__name__)


class AdminCog(commands.Cog, name="Admin"):
    def __init__(self, bot: CazalbertoBot) -> None:
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        if await self.bot.is_owner(ctx.author):
            return True
        permissions = getattr(ctx.author, "guild_permissions", None)
        return bool(permissions and permissions.administrator)

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send("❌ Você precisa ser administrador para usar este comando!")
        else:
            log.error("Erro em !%s", ctx.command, exc_info=error)
            await ctx.send("❌ Erro inesperado. Veja o log do bot.")

    @commands.command(name="sync")
    async def sync(self, ctx: commands.Context, scope: str = "global") -> None:
        """!sync -> global (pode levar até 1h para aparecer) | !sync aqui -> só neste servidor (na hora)."""
        async with ctx.typing():
            if scope in {"aqui", "guild", "servidor"} and ctx.guild is not None:
                self.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await self.bot.tree.sync(guild=ctx.guild)
                where = "neste servidor"
            else:
                synced = await self.bot.tree.sync()
                where = "globalmente"
        names = ", ".join(f"/{c.name}" for c in synced)
        await ctx.send(f"✅ {len(synced)} comandos sincronizados {where}: {names}"[:2000])

    @commands.command(name="recarregar")
    async def reload(self, ctx: commands.Context) -> None:
        """Relê o commands.json, as playlists e a pasta do WoW sem reiniciar o bot."""
        self.bot.library.load()
        self.bot.playlists.load()
        self.bot.wow.scan()
        await ctx.send(
            f"🔄 Recarregado: {len(self.bot.library)} áudios, "
            f"{len(self.bot.playlists.all())} playlists, {len(self.bot.wow)} trilhas do WoW."
        )


async def setup(bot: CazalbertoBot) -> None:
    await bot.add_cog(AdminCog(bot))
