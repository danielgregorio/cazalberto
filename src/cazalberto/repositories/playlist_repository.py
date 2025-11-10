"""
Repository para operações com playlists
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.audio import Audio, Playlist, PlaylistItem
from .base import BaseRepository


class PlaylistRepository(BaseRepository[Playlist]):
    """Repository especializado para playlists"""

    def __init__(self, session: AsyncSession):
        super().__init__(Playlist, session)

    async def get_by_name(self, name: str, guild_id: int) -> Playlist | None:
        """
        Busca uma playlist por nome e servidor

        Args:
            name: Nome da playlist
            guild_id: ID do servidor Discord

        Returns:
            Playlist ou None se não encontrada
        """
        stmt = (
            select(Playlist)
            .where(Playlist.name == name, Playlist.guild_id == guild_id)
            .options(selectinload(Playlist.items).selectinload(PlaylistItem.audio))
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_guild(self, guild_id: int) -> list[Playlist]:
        """
        Lista todas as playlists de um servidor

        Args:
            guild_id: ID do servidor Discord

        Returns:
            Lista de playlists
        """
        stmt = (
            select(Playlist)
            .where(Playlist.guild_id == guild_id)
            .order_by(Playlist.name)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_items(self, playlist_id: int) -> Playlist | None:
        """
        Busca uma playlist com seus items carregados

        Args:
            playlist_id: ID da playlist

        Returns:
            Playlist com items ou None
        """
        stmt = (
            select(Playlist)
            .where(Playlist.id == playlist_id)
            .options(selectinload(Playlist.items).selectinload(PlaylistItem.audio))
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_audio(
        self, playlist_id: int, audio_id: int, position: int | None = None
    ) -> PlaylistItem:
        """
        Adiciona um áudio à playlist

        Args:
            playlist_id: ID da playlist
            audio_id: ID do áudio
            position: Posição na playlist (None = final)

        Returns:
            PlaylistItem criado
        """
        # Se position não especificada, adiciona no final
        if position is None:
            stmt = select(PlaylistItem).where(
                PlaylistItem.playlist_id == playlist_id
            )
            result = await self.session.execute(stmt)
            items = result.scalars().all()
            position = len(items)

        item = PlaylistItem(
            playlist_id=playlist_id, audio_id=audio_id, position=position
        )

        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def remove_audio(self, playlist_id: int, audio_id: int) -> bool:
        """
        Remove um áudio da playlist

        Args:
            playlist_id: ID da playlist
            audio_id: ID do áudio

        Returns:
            True se removido, False se não encontrado
        """
        stmt = select(PlaylistItem).where(
            PlaylistItem.playlist_id == playlist_id,
            PlaylistItem.audio_id == audio_id,
        )

        result = await self.session.execute(stmt)
        item = result.scalar_one_or_none()

        if item:
            await self.session.delete(item)
            await self.session.commit()

            # Reorganizar posições
            await self._reorder_items(playlist_id)
            return True

        return False

    async def _reorder_items(self, playlist_id: int) -> None:
        """
        Reorganiza as posições dos items sequencialmente

        Args:
            playlist_id: ID da playlist
        """
        stmt = (
            select(PlaylistItem)
            .where(PlaylistItem.playlist_id == playlist_id)
            .order_by(PlaylistItem.position)
        )

        result = await self.session.execute(stmt)
        items = result.scalars().all()

        for index, item in enumerate(items):
            item.position = index

        await self.session.commit()

    async def get_audios(self, playlist_id: int) -> list[Audio]:
        """
        Retorna lista de áudios da playlist em ordem

        Args:
            playlist_id: ID da playlist

        Returns:
            Lista de áudios
        """
        playlist = await self.get_with_items(playlist_id)

        if not playlist:
            return []

        # Items já vêm ordenados por position
        return [item.audio for item in playlist.items]

    async def playlist_exists(self, name: str, guild_id: int) -> bool:
        """
        Verifica se uma playlist existe

        Args:
            name: Nome da playlist
            guild_id: ID do servidor

        Returns:
            True se existe
        """
        playlist = await self.get_by_name(name, guild_id)
        return playlist is not None
