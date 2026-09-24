"""Funções de texto: normalização de nomes e divisão de mensagens."""

from __future__ import annotations

import re
import unicodedata

DISCORD_MESSAGE_LIMIT = 2000


def slugify(text: str) -> str:
    """'Dalaran (Jaina)' -> 'dalaran-jaina'. Remove acentos e pontuação."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower().replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def normalize_name(name: str) -> str:
    """Normaliza o nome digitado pelo usuário para buscar comandos e playlists."""
    return " ".join(name.lower().split())


def truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def chunk_lines(text: str, limit: int = 1900) -> list[str]:
    """Divide um texto por linhas em pedaços que cabem numa mensagem do Discord."""
    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        while len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > limit:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks
