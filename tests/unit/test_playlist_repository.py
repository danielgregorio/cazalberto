"""
Testes para PlaylistRepository
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.cazalberto.models.audio import Audio, Playlist
from src.cazalberto.repositories.playlist_repository import PlaylistRepository


@pytest.mark.asyncio
async def test_create_playlist(session: AsyncSession, sample_playlist: Playlist) -> None:
    """Testa criação de uma playlist"""
    repo = PlaylistRepository(session)

    created = await repo.create(
        name=sample_playlist.name,
        description=sample_playlist.description,
        guild_id=sample_playlist.guild_id,
        created_by=sample_playlist.created_by,
    )

    assert created.id is not None
    assert created.name == sample_playlist.name
    assert created.description == sample_playlist.description


@pytest.mark.asyncio
async def test_get_by_name(session: AsyncSession, sample_playlist: Playlist) -> None:
    """Testa busca por nome"""
    repo = PlaylistRepository(session)

    session.add(sample_playlist)
    await session.commit()

    found = await repo.get_by_name(sample_playlist.name, sample_playlist.guild_id)

    assert found is not None
    assert found.name == sample_playlist.name


@pytest.mark.asyncio
async def test_list_by_guild(session: AsyncSession) -> None:
    """Testa listagem por servidor"""
    repo = PlaylistRepository(session)

    guild_id = 123456789

    # Criar playlists
    for i in range(3):
        playlist = Playlist(
            name=f"Playlist{i}",
            guild_id=guild_id,
            created_by=1,
        )
        session.add(playlist)

    await session.commit()

    playlists = await repo.list_by_guild(guild_id)

    assert len(playlists) == 3


@pytest.mark.asyncio
async def test_add_audio_to_playlist(
    session: AsyncSession, sample_playlist: Playlist, sample_audio: Audio
) -> None:
    """Testa adição de áudio à playlist"""
    repo = PlaylistRepository(session)

    # Criar playlist e áudio
    session.add(sample_playlist)
    session.add(sample_audio)
    await session.commit()

    # Adicionar áudio
    item = await repo.add_audio(sample_playlist.id, sample_audio.id)

    assert item is not None
    assert item.playlist_id == sample_playlist.id
    assert item.audio_id == sample_audio.id
    assert item.position == 0  # Primeira posição


@pytest.mark.asyncio
async def test_remove_audio_from_playlist(
    session: AsyncSession, sample_playlist: Playlist, sample_audio: Audio
) -> None:
    """Testa remoção de áudio da playlist"""
    repo = PlaylistRepository(session)

    # Criar playlist e áudio
    session.add(sample_playlist)
    session.add(sample_audio)
    await session.commit()

    # Adicionar áudio
    await repo.add_audio(sample_playlist.id, sample_audio.id)

    # Remover
    removed = await repo.remove_audio(sample_playlist.id, sample_audio.id)

    assert removed is True

    # Verificar que foi removido
    playlist = await repo.get_with_items(sample_playlist.id)
    assert len(playlist.items) == 0  # type: ignore


@pytest.mark.asyncio
async def test_get_audios(
    session: AsyncSession, sample_playlist: Playlist
) -> None:
    """Testa obtenção da lista de áudios"""
    repo = PlaylistRepository(session)

    # Criar playlist
    session.add(sample_playlist)
    await session.commit()

    # Criar e adicionar áudios
    for i in range(3):
        audio = Audio(
            command=f"cmd{i}",
            file_path=f"audio{i}.mp3",
            guild_id=sample_playlist.guild_id,
            added_by=1,
        )
        session.add(audio)
        await session.flush()

        await repo.add_audio(sample_playlist.id, audio.id)

    # Obter áudios
    audios = await repo.get_audios(sample_playlist.id)

    assert len(audios) == 3
    assert audios[0].command == "cmd0"
    assert audios[1].command == "cmd1"
    assert audios[2].command == "cmd2"


@pytest.mark.asyncio
async def test_playlist_exists(
    session: AsyncSession, sample_playlist: Playlist
) -> None:
    """Testa verificação de existência"""
    repo = PlaylistRepository(session)

    # Não existe
    exists = await repo.playlist_exists(sample_playlist.name, sample_playlist.guild_id)
    assert exists is False

    # Criar
    session.add(sample_playlist)
    await session.commit()

    # Agora existe
    exists = await repo.playlist_exists(sample_playlist.name, sample_playlist.guild_id)
    assert exists is True
