"""
Gerenciamento de conexão com o banco de dados
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..models.base import Base
from .config import settings
from .logging import get_logger

logger = get_logger("database")

# Engine global
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Retorna a engine do SQLAlchemy (singleton)

    Returns:
        AsyncEngine configurado
    """
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.log_level == "DEBUG",
            pool_pre_ping=True,  # Verifica conexão antes de usar
            pool_size=5,
            max_overflow=10,
        )
        logger.info(f"Engine criada: {settings.database_url}")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Retorna a factory de sessões (singleton)

    Returns:
        Session factory
    """
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        logger.info("Session factory criada")
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obter uma sessão do banco de dados

    Yields:
        AsyncSession
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Inicializa o banco de dados criando todas as tabelas

    Útil para desenvolvimento. Em produção use Alembic migrations.
    """
    engine = get_engine()
    logger.info("Criando tabelas do banco de dados...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("✓ Tabelas criadas com sucesso")


async def drop_db() -> None:
    """
    Remove todas as tabelas do banco de dados

    ⚠️ CUIDADO: Isso remove TODOS os dados!
    """
    engine = get_engine()
    logger.warning("Removendo TODAS as tabelas do banco de dados...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    logger.warning("✓ Tabelas removidas")


async def close_db() -> None:
    """
    Fecha a conexão com o banco de dados
    """
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        logger.info("Conexão com banco de dados fechada")
        _engine = None
        _session_factory = None
