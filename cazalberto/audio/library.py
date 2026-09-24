"""Biblioteca de áudios personalizados (os que o pessoal ensina com /aprender)."""

from __future__ import annotations

import logging
import re
from pathlib import Path, PurePosixPath, PureWindowsPath

from ..errors import UserError
from ..storage import load_json, save_json
from ..text import normalize_name, slugify

log = logging.getLogger(__name__)

NAME_PATTERN = re.compile(r"^[\w\- ]{1,32}$")
LEGACY_AUDIO_PREFIX = "audio_clips"


def _normalize_stored_path(raw: str) -> str:
    """Converte caminhos antigos no formato do Windows para o formato portátil.

    'audio_clips\\quico.mp3' vira 'quico.mp3' (relativo à pasta de áudios), assim
    o mesmo commands.json funciona no Windows, no Linux e no Docker.
    Caminhos absolutos (ex.: 'D:\\musicas\\x.mp3') são mantidos como estão.
    """
    windows = PureWindowsPath(raw)
    if windows.drive or raw.startswith("/"):
        return raw
    parts = PurePosixPath(*windows.parts).parts
    if parts and parts[0] == LEGACY_AUDIO_PREFIX:
        parts = parts[1:]
    return str(PurePosixPath(*parts)) if parts else raw


class AudioLibrary:
    def __init__(self, commands_file: Path, audio_dir: Path) -> None:
        self.commands_file = commands_file
        self.audio_dir = audio_dir
        self._entries: dict[str, str] = {}

    def load(self) -> None:
        raw = load_json(self.commands_file, {})
        if not isinstance(raw, dict):
            log.error("%s não é um objeto JSON; ignorando conteúdo.", self.commands_file)
            raw = {}
        entries = {
            normalize_name(name): _normalize_stored_path(path)
            for name, path in raw.items()
            if isinstance(name, str) and isinstance(path, str)
        }
        changed = entries != raw
        self._entries = dict(sorted(entries.items()))
        if changed and self._entries:
            log.info("Migrando %s para o formato portátil.", self.commands_file)
            self.save()
        log.info("%d áudios carregados de %s", len(self._entries), self.commands_file)

    def save(self) -> None:
        save_json(self.commands_file, self._entries)

    def __contains__(self, name: str) -> bool:
        return normalize_name(name) in self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def names(self) -> list[str]:
        return list(self._entries)

    def resolve(self, name: str) -> Path | None:
        stored = self._entries.get(normalize_name(name))
        if stored is None:
            return None
        path = Path(stored)
        return path if path.is_absolute() else self.audio_dir / path

    @staticmethod
    def validate_name(name: str) -> str:
        name = normalize_name(name)
        if not NAME_PATTERN.fullmatch(name):
            raise UserError(
                "❌ O nome deve ter de 1 a 32 caracteres: letras, números, espaço, `-` ou `_`."
            )
        return name

    def target_path(self, name: str, suffix: str = ".mp3") -> Path:
        """Caminho do arquivo para um áudio novo, sempre dentro da pasta de áudios."""
        filename = (slugify(name) or "audio") + suffix
        candidate = self.audio_dir / filename
        counter = 2
        while candidate.exists():
            candidate = self.audio_dir / f"{slugify(name) or 'audio'}-{counter}{suffix}"
            counter += 1
        return candidate

    def add(self, name: str, path: Path) -> None:
        name = self.validate_name(name)
        if name in self._entries:
            raise UserError(f"❌ O comando `{name}` já existe!")
        try:
            stored = str(PurePosixPath(*path.resolve().relative_to(self.audio_dir.resolve()).parts))
        except ValueError:
            stored = str(path)
        self._entries[name] = stored
        self._entries = dict(sorted(self._entries.items()))
        self.save()

    def remove(self, name: str) -> Path | None:
        """Remove o comando e devolve o arquivo que pode ser apagado (apenas se
        estiver dentro da pasta de áudios do bot e não for usado por outro comando)."""
        name = normalize_name(name)
        if name not in self._entries:
            raise UserError(f"❌ O comando `{name}` não existe!")
        path = self.resolve(name)
        stored = self._entries.pop(name)
        self.save()

        if path is None or stored in self._entries.values():
            return None
        try:
            path.resolve().relative_to(self.audio_dir.resolve())
        except ValueError:
            return None
        return path
