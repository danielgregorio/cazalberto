"""Configuração de logs, feita uma única vez na inicialização."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging(level: str = "INFO", log_file: Path | None = None) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        # Até ~5 MB por arquivo, mantendo 3 antigos, para o log não crescer para sempre.
        handlers.append(
            RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
        )
    logging.basicConfig(level=level, format=FORMAT, handlers=handlers, force=True)
    logging.getLogger("discord").setLevel(max(logging.getLevelName(level), logging.INFO))
