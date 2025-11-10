"""
Script para migrar dados de JSON para SQLite

Usage:
    python -m cazalberto.scripts.migrate_json_to_db [--commands-json PATH] [--playlists-json PATH]
"""

import argparse
import asyncio
import json
from pathlib import Path

from ..core.config import settings
from ..core.database import get_session_factory, init_db
from ..core.logging import get_logger, setup_logging
from ..models.audio import Audio, Playlist, PlaylistItem
from ..repositories.audio_repository import AudioRepository
from ..repositories.playlist_repository import PlaylistRepository

logger = get_logger("migrate")


async def migrate_commands_json(json_path: Path) -> int:
    """
    Migra commands.json para o banco de dados

    Args:
        json_path: Caminho do arquivo commands.json

    Returns:
        Número de comandos migrados
    """
    if not json_path.exists():
        logger.warning(f"Arquivo não encontrado: {json_path}")
        return 0

    logger.info(f"Lendo {json_path}...")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"Encontrados {len(data)} comandos")

    session_factory = get_session_factory()
    count = 0

    async with session_factory() as session:
        repo = AudioRepository(session)

        for command, file_path in data.items():
            # Normalizar path (remover barras invertidas do Windows)
            file_path_normalized = file_path.replace("\\", "/")

            # Verificar se já existe
            if await repo.command_exists(command, guild_id=0):
                logger.debug(f"Comando já existe: {command}")
                continue

            # Criar áudio
            try:
                audio = Audio(
                    command=command,
                    file_path=file_path_normalized,
                    guild_id=0,  # Global
                    added_by=0,  # System
                    play_count=0,
                )
                session.add(audio)
                count += 1
                logger.debug(f"Migrado: {command} -> {file_path_normalized}")

            except Exception as e:
                logger.error(f"Erro ao migrar comando '{command}': {e}")

        await session.commit()

    logger.info(f"✓ {count} comandos migrados com sucesso")
    return count


async def migrate_playlists_json(json_path: Path) -> int:
    """
    Migra playlists.json para o banco de dados

    Args:
        json_path: Caminho do arquivo playlists.json

    Returns:
        Número de playlists migradas
    """
    if not json_path.exists():
        logger.warning(f"Arquivo não encontrado: {json_path}")
        return 0

    logger.info(f"Lendo {json_path}...")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"Encontradas {len(data)} playlists")

    session_factory = get_session_factory()
    count = 0

    async with session_factory() as session:
        playlist_repo = PlaylistRepository(session)
        audio_repo = AudioRepository(session)

        for playlist_name, audio_commands in data.items():
            # Verificar se já existe
            if await playlist_repo.playlist_exists(playlist_name, guild_id=0):
                logger.debug(f"Playlist já existe: {playlist_name}")
                continue

            # Criar playlist
            try:
                playlist = Playlist(
                    name=playlist_name,
                    guild_id=0,  # Global
                    created_by=0,  # System
                )
                session.add(playlist)
                await session.flush()  # Para obter o ID

                # Adicionar áudios
                for position, command in enumerate(audio_commands):
                    audio = await audio_repo.get_by_command(command, guild_id=0)

                    if audio:
                        item = PlaylistItem(
                            playlist_id=playlist.id,
                            audio_id=audio.id,
                            position=position,
                        )
                        session.add(item)
                    else:
                        logger.warning(
                            f"Áudio '{command}' não encontrado para playlist '{playlist_name}'"
                        )

                count += 1
                logger.debug(f"Migrada: {playlist_name} ({len(audio_commands)} áudios)")

            except Exception as e:
                logger.error(f"Erro ao migrar playlist '{playlist_name}': {e}")

        await session.commit()

    logger.info(f"✓ {count} playlists migradas com sucesso")
    return count


async def main() -> None:
    """Função principal"""
    setup_logging()

    parser = argparse.ArgumentParser(description="Migrar dados JSON para SQLite")
    parser.add_argument(
        "--commands-json",
        type=Path,
        default=Path("commands.json"),
        help="Caminho do arquivo commands.json",
    )
    parser.add_argument(
        "--playlists-json",
        type=Path,
        default=Path("playlists.json"),
        help="Caminho do arquivo playlists.json",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Inicializar banco de dados (criar tabelas)",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Iniciando migração JSON → SQLite")
    logger.info("=" * 60)

    # Inicializar banco se necessário
    if args.init_db:
        logger.info("Inicializando banco de dados...")
        await init_db()

    # Migrar comandos
    commands_count = await migrate_commands_json(args.commands_json)

    # Migrar playlists
    playlists_count = await migrate_playlists_json(args.playlists_json)

    # Resumo
    logger.info("=" * 60)
    logger.info("Migração concluída!")
    logger.info(f"  Comandos migrados: {commands_count}")
    logger.info(f"  Playlists migradas: {playlists_count}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
