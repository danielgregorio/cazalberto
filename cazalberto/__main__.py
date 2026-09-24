"""Ponto de entrada: `python -m cazalberto` (ou `python bot.py`)."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from .config import ConfigError, Settings
from .logging_setup import setup_logging

log = logging.getLogger("cazalberto")


async def _sync_only(settings: Settings) -> None:
    from .bot import CazalbertoBot

    bot = CazalbertoBot(settings)
    async with bot:
        await bot.login(settings.token)  # login já executa o setup_hook (carrega os cogs)
        if not settings.sync_on_startup:
            await bot.sync_commands()


async def _run(settings: Settings) -> None:
    from .bot import CazalbertoBot

    async with CazalbertoBot(settings) as bot:
        await bot.start(settings.token)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cazalberto", description="Bot de áudio para Discord.")
    parser.add_argument(
        "--sync",
        action="store_true",
        help="registra os comandos slash no Discord e sai (sem ficar online)",
    )
    args = parser.parse_args(argv)

    try:
        settings = Settings.from_env()
    except ConfigError as exc:
        print(f"Erro de configuração: {exc}", file=sys.stderr)
        return 2

    setup_logging(settings.log_level, settings.log_file)
    try:
        asyncio.run(_sync_only(settings) if args.sync else _run(settings))
    except KeyboardInterrupt:
        log.info("Encerrado pelo usuário.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
