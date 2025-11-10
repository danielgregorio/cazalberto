"""
Fixtures para testes de integração do painel web
"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.cazalberto.core.database import get_session
from src.cazalberto.models.audio import Audio, Playlist
from src.cazalberto.models.base import Base
from src.cazalberto.web.app import app


@pytest_asyncio.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Engine de teste em memória separada para testes de integração
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def override_get_session(
    test_engine: AsyncEngine,
) -> AsyncGenerator[callable, None]:
    """
    Sobrescreve a dependência get_session para usar banco de teste
    """
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def _get_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    yield _get_session


@pytest_asyncio.fixture
async def test_app(
    test_engine: AsyncEngine, override_get_session: callable
) -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP de teste para a aplicação FastAPI

    Usa banco de dados em memória e sobrescreve dependências
    """
    # Sobrescrever dependência de sessão
    app.dependency_overrides[get_session] = override_get_session

    # Criar cliente HTTP assíncrono
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Limpar overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_app_with_data(
    test_app: AsyncClient, test_engine: AsyncEngine
) -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP com dados de teste pré-populados
    """
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
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
