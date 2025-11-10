"""
Fixtures para testes de integração do painel web
"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from src.cazalberto.core.database import get_session_factory, init_db
from src.cazalberto.models.audio import Audio, Playlist
from src.cazalberto.web.app import app


@pytest_asyncio.fixture
async def test_app(engine: AsyncEngine) -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP de teste para a aplicação FastAPI

    Usa o mesmo banco de dados em memória dos testes unitários
    """
    # Inicializar banco
    await init_db()

    # Criar cliente HTTP assíncrono
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_app_with_data(
    test_app: AsyncClient, engine: AsyncEngine
) -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP com dados de teste pré-populados
    """
    session_factory = get_session_factory()

    async with session_factory() as session:
        # Criar áudios de teste
        audios = [
            Audio(
                command=f"audio{i}",
                file_path=f"audio_clips/audio{i}.mp3",
                guild_id=0 if i < 3 else 123,
                added_by=1,
                play_count=i * 10,
            )
            for i in range(5)
        ]

        for audio in audios:
            session.add(audio)

        # Criar playlist de teste
        playlist = Playlist(
            name="Test Playlist",
            description="Playlist de teste",
            guild_id=0,
            created_by=1,
        )
        session.add(playlist)

        await session.commit()

    yield test_app
