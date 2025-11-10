"""
Repository para operações com áudios
"""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audio import Audio
from .base import BaseRepository


class AudioRepository(BaseRepository[Audio]):
    """Repository especializado para áudios"""

    def __init__(self, session: AsyncSession):
        super().__init__(Audio, session)

    async def get_by_command(self, command: str, guild_id: int) -> Audio | None:
        """
        Busca um áudio por comando e servidor

        Args:
            command: Nome do comando
            guild_id: ID do servidor Discord (0 = global)

        Returns:
            Audio ou None se não encontrado
        """
        stmt = (
            select(Audio)
            .where(
                Audio.command == command,
                or_(Audio.guild_id == guild_id, Audio.guild_id == 0),
            )
            .order_by(Audio.guild_id.desc())  # Prioriza guild-specific sobre global
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_guild(
        self, guild_id: int, include_global: bool = True
    ) -> list[Audio]:
        """
        Lista todos os áudios de um servidor

        Args:
            guild_id: ID do servidor Discord
            include_global: Se deve incluir áudios globais

        Returns:
            Lista de áudios
        """
        conditions = [Audio.guild_id == guild_id]

        if include_global:
            conditions.append(Audio.guild_id == 0)

        stmt = select(Audio).where(or_(*conditions)).order_by(Audio.command)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_command(self, query: str, guild_id: int) -> list[Audio]:
        """
        Busca áudios por comando parcial (LIKE)

        Args:
            query: Termo de busca
            guild_id: ID do servidor

        Returns:
            Lista de áudios que correspondem
        """
        stmt = (
            select(Audio)
            .where(
                Audio.command.like(f"%{query}%"),
                or_(Audio.guild_id == guild_id, Audio.guild_id == 0),
            )
            .order_by(Audio.command)
            .limit(25)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def increment_play_count(self, audio_id: int) -> None:
        """
        Incrementa o contador de reproduções

        Args:
            audio_id: ID do áudio
        """
        audio = await self.get(audio_id)
        if audio:
            audio.play_count += 1
            await self.session.commit()

    async def get_most_played(
        self, guild_id: int, limit: int = 10
    ) -> list[Audio]:
        """
        Retorna os áudios mais reproduzidos

        Args:
            guild_id: ID do servidor
            limit: Quantidade máxima

        Returns:
            Lista de áudios ordenados por play_count
        """
        stmt = (
            select(Audio)
            .where(or_(Audio.guild_id == guild_id, Audio.guild_id == 0))
            .order_by(Audio.play_count.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_command(self, command: str, guild_id: int) -> bool:
        """
        Remove um áudio por comando

        Args:
            command: Nome do comando
            guild_id: ID do servidor

        Returns:
            True se removido, False se não encontrado
        """
        audio = await self.get_by_command(command, guild_id)
        if audio and audio.guild_id == guild_id:  # Só remove se for do servidor
            await self.session.delete(audio)
            await self.session.commit()
            return True
        return False

    async def command_exists(self, command: str, guild_id: int) -> bool:
        """
        Verifica se um comando já existe

        Args:
            command: Nome do comando
            guild_id: ID do servidor

        Returns:
            True se existe
        """
        audio = await self.get_by_command(command, guild_id)
        return audio is not None
