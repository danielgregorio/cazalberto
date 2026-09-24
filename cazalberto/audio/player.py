"""Conexão de voz e reprodução de áudio, compartilhada por todos os cogs."""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path

import discord

from ..errors import UserError

log = logging.getLogger(__name__)


class VoicePlayer:
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot
        # Uma fila (playlist) em andamento por servidor.
        self._queues: dict[int, asyncio.Task[None]] = {}

    def voice_client(self, guild: discord.Guild | None) -> discord.VoiceClient | None:
        if guild is None:
            return None
        vc = guild.voice_client
        return vc if isinstance(vc, discord.VoiceClient) and vc.is_connected() else None

    async def connect(self, interaction: discord.Interaction) -> discord.VoiceClient:
        """Conecta (ou move) o bot para o canal de voz de quem chamou o comando."""
        if interaction.guild is None:
            raise UserError("❌ Esse comando só funciona dentro de um servidor.")
        member = interaction.user
        channel = getattr(getattr(member, "voice", None), "channel", None)
        if channel is None:
            raise UserError("❌ Você precisa estar em um canal de voz!")

        vc = self.voice_client(interaction.guild)
        if vc is None:
            return await channel.connect()
        if vc.channel != channel:
            await vc.move_to(channel)
        return vc

    async def play(self, vc: discord.VoiceClient, path: Path, *, wait: bool = False) -> None:
        """Toca um arquivo, interrompendo o que estiver tocando.
        Com `wait=True`, só retorna quando o áudio termina."""
        if not path.is_file():
            raise UserError(f"❌ Arquivo de áudio não encontrado: `{path.name}`")

        loop = asyncio.get_running_loop()
        finished = asyncio.Event()

        def after(error: Exception | None) -> None:
            if error:
                log.error("Erro durante a reprodução de %s: %s", path, error)
            loop.call_soon_threadsafe(finished.set)

        if vc.is_playing() or vc.is_paused():
            vc.stop()
        vc.play(discord.FFmpegPCMAudio(str(path)), after=after)
        log.info("Tocando %s em %s", path.name, vc.guild.name)
        if wait:
            await finished.wait()

    def cancel_queue(self, guild_id: int) -> bool:
        task = self._queues.pop(guild_id, None)
        if task is not None and not task.done():
            task.cancel()
            return True
        return False

    def start_queue(
        self,
        vc: discord.VoiceClient,
        items: Sequence[tuple[str, Path]],
        *,
        repeat: int = 1,
        shuffle: bool = False,
        on_track: Callable[[str], Awaitable[None]] | None = None,
        on_finish: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        """Toca vários áudios em sequência em segundo plano. Uma nova fila no
        mesmo servidor cancela a anterior."""
        guild_id = vc.guild.id
        self.cancel_queue(guild_id)

        async def run() -> None:
            try:
                for _ in range(repeat):
                    order = list(items)
                    if shuffle:
                        random.shuffle(order)
                    for name, path in order:
                        if not vc.is_connected():
                            return
                        if on_track:
                            await _safe(on_track(name))
                        try:
                            await self.play(vc, path, wait=True)
                        except UserError as exc:
                            log.warning("Pulando %s: %s", name, exc)
                if on_finish:
                    await _safe(on_finish())
            finally:
                if self._queues.get(guild_id) is asyncio.current_task():
                    del self._queues[guild_id]

        self._queues[guild_id] = asyncio.create_task(run(), name=f"queue-{guild_id}")

    async def stop(self, guild: discord.Guild) -> bool:
        self.cancel_queue(guild.id)
        vc = self.voice_client(guild)
        if vc is None:
            return False
        await vc.disconnect()
        return True


async def _safe(coro: Awaitable[None]) -> None:
    """Mensagens de progresso não podem derrubar a reprodução."""
    try:
        await coro
    except discord.HTTPException as exc:
        log.warning("Falha ao enviar mensagem de progresso: %s", exc)
