"""Lista paginada de áudios com um botão para tocar cada um."""

from __future__ import annotations

import contextlib
import math
from collections.abc import Awaitable, Callable, Sequence

import discord
from discord import ui

from ..text import truncate

PAGE_SIZE = 20  # 4 linhas de 5 botões; a 5ª linha fica para a navegação
BUTTONS_PER_ROW = 5
LABEL_LIMIT = 24

PlayCallback = Callable[[discord.Interaction, str], Awaitable[None]]


class AudioBrowser(ui.View):
    def __init__(
        self,
        names: Sequence[str],
        on_play: PlayCallback,
        *,
        strip_prefix: bool = False,
        page: int = 0,
        timeout: float = 300,
    ) -> None:
        super().__init__(timeout=timeout)
        self.names = list(names)
        self.on_play = on_play
        self.strip_prefix = strip_prefix
        self.total_pages = max(1, math.ceil(len(self.names) / PAGE_SIZE))
        self.page = min(max(page, 0), self.total_pages - 1)
        self.message: discord.Message | None = None
        self._render()

    def _label(self, name: str) -> str:
        if self.strip_prefix and "-" in name:
            name = name.split("-", 1)[1]
        return truncate(name, LABEL_LIMIT)

    def _render(self) -> None:
        self.clear_items()
        start = self.page * PAGE_SIZE
        for i, name in enumerate(self.names[start : start + PAGE_SIZE]):
            button = ui.Button(
                style=discord.ButtonStyle.primary,
                label=self._label(name),
                row=i // BUTTONS_PER_ROW,
            )
            button.callback = self._make_play_callback(name)
            self.add_item(button)

        if self.total_pages > 1:
            previous = ui.Button(
                label="◀", style=discord.ButtonStyle.secondary, row=4, disabled=self.page == 0
            )
            previous.callback = self._make_page_callback(-1)
            indicator = ui.Button(
                label=f"{self.page + 1}/{self.total_pages}",
                style=discord.ButtonStyle.secondary,
                row=4,
                disabled=True,
            )
            following = ui.Button(
                label="▶",
                style=discord.ButtonStyle.secondary,
                row=4,
                disabled=self.page >= self.total_pages - 1,
            )
            following.callback = self._make_page_callback(+1)
            for item in (previous, indicator, following):
                self.add_item(item)

    def _make_play_callback(self, name: str):
        async def callback(interaction: discord.Interaction) -> None:
            await self.on_play(interaction, name)

        return callback

    def _make_page_callback(self, delta: int):
        async def callback(interaction: discord.Interaction) -> None:
            self.page = min(max(self.page + delta, 0), self.total_pages - 1)
            self._render()
            await interaction.response.edit_message(view=self)

        return callback

    async def on_timeout(self) -> None:
        if self.message is not None:
            for item in self.children:
                if isinstance(item, ui.Button):
                    item.disabled = True
            with contextlib.suppress(discord.HTTPException):
                await self.message.edit(view=self)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception, item: ui.Item
    ) -> None:
        # Mesmo tratamento dos comandos slash (UserError vira mensagem para o usuário).
        await interaction.client.report_error(interaction, error)
