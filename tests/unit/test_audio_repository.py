"""
Testes para AudioRepository
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.cazalberto.models.audio import Audio
from src.cazalberto.repositories.audio_repository import AudioRepository


@pytest.mark.asyncio
async def test_create_audio(session: AsyncSession, sample_audio: Audio) -> None:
    """Testa criação de um áudio"""
    repo = AudioRepository(session)

    created = await repo.create(
        command=sample_audio.command,
        file_path=sample_audio.file_path,
        guild_id=sample_audio.guild_id,
        added_by=sample_audio.added_by,
    )

    assert created.id is not None
    assert created.command == sample_audio.command
    assert created.file_path == sample_audio.file_path
    assert created.play_count == 0


@pytest.mark.asyncio
async def test_get_by_command(session: AsyncSession, sample_audio: Audio) -> None:
    """Testa busca por comando"""
    repo = AudioRepository(session)

    # Criar áudio
    session.add(sample_audio)
    await session.commit()

    # Buscar
    found = await repo.get_by_command(sample_audio.command, sample_audio.guild_id)

    assert found is not None
    assert found.command == sample_audio.command
    assert found.guild_id == sample_audio.guild_id


@pytest.mark.asyncio
async def test_get_by_command_not_found(session: AsyncSession) -> None:
    """Testa busca por comando inexistente"""
    repo = AudioRepository(session)

    found = await repo.get_by_command("inexistente", 123)

    assert found is None


@pytest.mark.asyncio
async def test_list_by_guild(session: AsyncSession) -> None:
    """Testa listagem por servidor"""
    repo = AudioRepository(session)

    guild_id = 123456789

    # Criar áudios
    for i in range(3):
        audio = Audio(
            command=f"cmd{i}",
            file_path=f"audio{i}.mp3",
            guild_id=guild_id,
            added_by=1,
        )
        session.add(audio)

    # Adicionar um global
    global_audio = Audio(
        command="global",
        file_path="global.mp3",
        guild_id=0,
        added_by=1,
    )
    session.add(global_audio)

    await session.commit()

    # Buscar
    audios = await repo.list_by_guild(guild_id, include_global=True)

    assert len(audios) == 4  # 3 do guild + 1 global

    # Sem globais
    audios_no_global = await repo.list_by_guild(guild_id, include_global=False)

    assert len(audios_no_global) == 3


@pytest.mark.asyncio
async def test_search_by_command(session: AsyncSession) -> None:
    """Testa busca parcial por comando"""
    repo = AudioRepository(session)

    guild_id = 123456789

    # Criar áudios
    commands = ["ola", "olá-pessoal", "teste", "olamundo"]
    for cmd in commands:
        audio = Audio(
            command=cmd,
            file_path=f"{cmd}.mp3",
            guild_id=guild_id,
            added_by=1,
        )
        session.add(audio)

    await session.commit()

    # Buscar por "ola"
    results = await repo.search_by_command("ola", guild_id)

    # Deve retornar 3: ola, olá-pessoal, olamundo
    assert len(results) == 3


@pytest.mark.asyncio
async def test_increment_play_count(session: AsyncSession, sample_audio: Audio) -> None:
    """Testa incremento do contador de reproduções"""
    repo = AudioRepository(session)

    session.add(sample_audio)
    await session.commit()

    initial_count = sample_audio.play_count

    # Incrementar
    await repo.increment_play_count(sample_audio.id)

    # Recarregar
    await session.refresh(sample_audio)

    assert sample_audio.play_count == initial_count + 1


@pytest.mark.asyncio
async def test_get_most_played(session: AsyncSession) -> None:
    """Testa busca dos mais reproduzidos"""
    repo = AudioRepository(session)

    guild_id = 123456789

    # Criar áudios com diferentes play_counts
    play_counts = [10, 5, 20, 3, 15]
    for i, count in enumerate(play_counts):
        audio = Audio(
            command=f"cmd{i}",
            file_path=f"audio{i}.mp3",
            guild_id=guild_id,
            added_by=1,
            play_count=count,
        )
        session.add(audio)

    await session.commit()

    # Buscar top 3
    most_played = await repo.get_most_played(guild_id, limit=3)

    assert len(most_played) == 3
    assert most_played[0].play_count == 20
    assert most_played[1].play_count == 15
    assert most_played[2].play_count == 10


@pytest.mark.asyncio
async def test_delete_by_command(session: AsyncSession, sample_audio: Audio) -> None:
    """Testa remoção por comando"""
    repo = AudioRepository(session)

    session.add(sample_audio)
    await session.commit()

    # Remover
    deleted = await repo.delete_by_command(sample_audio.command, sample_audio.guild_id)

    assert deleted is True

    # Verificar que foi removido
    found = await repo.get_by_command(sample_audio.command, sample_audio.guild_id)
    assert found is None


@pytest.mark.asyncio
async def test_command_exists(session: AsyncSession, sample_audio: Audio) -> None:
    """Testa verificação de existência de comando"""
    repo = AudioRepository(session)

    # Não existe
    exists = await repo.command_exists(sample_audio.command, sample_audio.guild_id)
    assert exists is False

    # Criar
    session.add(sample_audio)
    await session.commit()

    # Agora existe
    exists = await repo.command_exists(sample_audio.command, sample_audio.guild_id)
    assert exists is True
