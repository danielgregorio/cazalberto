"""
Models relacionados a áudios
"""

from sqlalchemy import BigInteger, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Audio(BaseModel):
    """Model para armazenar informações de áudio"""

    __tablename__ = "audios"

    # Comando usado para reproduzir o áudio
    command: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Caminho do arquivo de áudio
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # ID do servidor Discord (0 = global)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, default=0)

    # ID do usuário que adicionou
    added_by: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Contador de reproduções
    play_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Duração em segundos (opcional)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relacionamentos
    playlist_items: Mapped[list["PlaylistItem"]] = relationship(
        "PlaylistItem", back_populates="audio", cascade="all, delete-orphan"
    )

    play_history: Mapped[list["PlayHistory"]] = relationship(
        "PlayHistory", back_populates="audio", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Comando deve ser único por servidor
        UniqueConstraint("command", "guild_id", name="uq_audio_command_guild"),
        # Índice composto para queries comuns
        Index("idx_audio_guild_command", "guild_id", "command"),
    )

    def __repr__(self) -> str:
        return f"Audio(id={self.id}, command={self.command!r}, guild_id={self.guild_id})"


class PlayHistory(BaseModel):
    """Histórico de reprodução de áudios"""

    __tablename__ = "play_history"

    # Referência ao áudio
    audio_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )

    # ID do servidor Discord
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    # ID do usuário que reproduziu
    played_by: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # ID do canal de voz
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relacionamentos
    audio: Mapped["Audio"] = relationship("Audio", back_populates="play_history")

    __table_args__ = (
        # Índice para queries por servidor e data
        Index("idx_play_history_guild_date", "guild_id", "created_at"),
        # Índice para queries por áudio
        Index("idx_play_history_audio_date", "audio_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"PlayHistory(id={self.id}, audio_id={self.audio_id}, guild_id={self.guild_id})"


class Playlist(BaseModel):
    """Model para playlists de áudio"""

    __tablename__ = "playlists"

    # Nome da playlist
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Descrição opcional
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ID do servidor Discord
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    # ID do usuário criador
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relacionamentos
    items: Mapped[list["PlaylistItem"]] = relationship(
        "PlaylistItem",
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="PlaylistItem.position",
    )

    __table_args__ = (
        # Nome deve ser único por servidor
        UniqueConstraint("name", "guild_id", name="uq_playlist_name_guild"),
        # Índice composto
        Index("idx_playlist_guild_name", "guild_id", "name"),
    )

    def __repr__(self) -> str:
        return f"Playlist(id={self.id}, name={self.name!r}, guild_id={self.guild_id})"


class PlaylistItem(BaseModel):
    """Items de uma playlist (relação many-to-many entre Playlist e Audio)"""

    __tablename__ = "playlist_items"

    # ID da playlist
    playlist_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )

    # ID do áudio
    audio_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )

    # Posição na playlist
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relacionamentos
    playlist: Mapped["Playlist"] = relationship("Playlist", back_populates="items")
    audio: Mapped["Audio"] = relationship("Audio", back_populates="playlist_items")

    __table_args__ = (
        # Áudio não pode aparecer duas vezes na mesma playlist
        UniqueConstraint("playlist_id", "audio_id", name="uq_playlist_audio"),
        # Índice para ordenação
        Index("idx_playlist_items_position", "playlist_id", "position"),
    )

    def __repr__(self) -> str:
        return f"PlaylistItem(playlist_id={self.playlist_id}, audio_id={self.audio_id}, position={self.position})"
