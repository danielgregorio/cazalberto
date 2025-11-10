"""
Script para inicializar o banco de dados

Usage:
    python -m cazalberto.scripts.init_db
"""

import asyncio

from ..core.database import init_db
from ..core.logging import get_logger, setup_logging

logger = get_logger("init_db")


async def main() -> None:
    """Inicializa o banco de dados"""
    setup_logging()

    logger.info("Inicializando banco de dados...")

    try:
        await init_db()
        logger.info("✓ Banco de dados inicializado com sucesso!")
    except Exception as e:
        logger.error(f"✗ Erro ao inicializar banco: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
