"""
Sistema de logging configurável
"""

import logging
import sys
from pathlib import Path
from typing import Any

from .config import settings


def setup_logging() -> logging.Logger:
    """
    Configura o sistema de logging da aplicação

    Returns:
        Logger principal do Cazalberto
    """
    # Criar logger principal
    logger = logging.getLogger("cazalberto")
    logger.setLevel(getattr(logging, settings.log_level))

    # Evitar duplicação de handlers
    if logger.handlers:
        return logger

    # Formato de log
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para arquivo
    try:
        settings.log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            settings.log_file, encoding="utf-8", mode="a"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Não foi possível criar arquivo de log: {e}")

    # Configurar logging do discord.py
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.INFO)

    logger.info(f"Logging inicializado - Nível: {settings.log_level}")
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger filho

    Args:
        name: Nome do módulo

    Returns:
        Logger configurado
    """
    return logging.getLogger(f"cazalberto.{name}")
