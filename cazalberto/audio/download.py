"""Download de áudios enviados por URL, com limite de tamanho."""

from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlparse

import aiohttp

from ..errors import UserError

log = logging.getLogger(__name__)

CHUNK_SIZE = 64 * 1024
ALLOWED_TYPES = ("audio/", "video/", "application/octet-stream")


async def download_audio(
    session: aiohttp.ClientSession, url: str, destination: Path, *, max_bytes: int
) -> None:
    """Baixa `url` para `destination`. O arquivo só aparece no destino final
    quando o download termina com sucesso."""
    if urlparse(url).scheme not in {"http", "https"}:
        raise UserError("❌ A URL precisa começar com http:// ou https://")

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    limit_mb = max_bytes // (1024 * 1024)

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status != 200:
                raise UserError(f"❌ Não consegui baixar o arquivo (HTTP {response.status}).")
            content_type = response.headers.get("Content-Type", "")
            if content_type and not content_type.startswith(ALLOWED_TYPES):
                raise UserError(f"❌ A URL não parece ser um áudio (tipo `{content_type}`).")
            if (response.content_length or 0) > max_bytes:
                raise UserError(f"❌ Arquivo grande demais (máximo {limit_mb} MB).")

            written = 0
            with partial.open("wb") as f:
                async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                    written += len(chunk)
                    if written > max_bytes:
                        raise UserError(f"❌ Arquivo grande demais (máximo {limit_mb} MB).")
                    f.write(chunk)
        partial.replace(destination)
        log.info("Áudio baixado: %s (%d bytes)", destination, written)
    except aiohttp.ClientError as exc:
        log.warning("Falha ao baixar %s: %s", url, exc)
        raise UserError("❌ Erro ao baixar o arquivo. Verifique se a URL é válida.") from exc
    finally:
        partial.unlink(missing_ok=True)
