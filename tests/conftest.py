"""
Fixtures compartilhadas para testes
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.cazalberto.models import Audio, Base, Playlist


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Cria um event loop para a sessão de testes"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """Cria uma engine de banco de dados em memória para testes"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Cria uma sessão de banco de dados para testes"""
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def sample_audio() -> Audio:
    """Fixture de áudio de exemplo"""
    return Audio(
        command="teste",
        file_path="audio_clips/teste.mp3",
        guild_id=123456789,
        added_by=987654321,
        play_count=0,
    )


@pytest.fixture
def sample_playlist() -> Playlist:
    """Fixture de playlist de exemplo"""
    return Playlist(
        name="Favoritas",
        description="Minha playlist favorita",
        guild_id=123456789,
        created_by=987654321,
    )
