"""Armazenamento das playlists (nome -> lista de comandos de áudio)."""

from __future__ import annotations

import logging
from pathlib import Path

from .errors import UserError
from .storage import load_json, save_json
from .text import normalize_name

log = logging.getLogger(__name__)

MAX_NAME_LENGTH = 32


class PlaylistStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._playlists: dict[str, list[str]] = {}

    def load(self) -> None:
        raw = load_json(self.path, {})
        # Formato antigo criado pelos scripts de Docker: {"playlists": []}
        if raw == {"playlists": []} or not isinstance(raw, dict):
            raw = {}
        self._playlists = {
            normalize_name(name): [str(item) for item in items]
            for name, items in raw.items()
            if isinstance(items, list)
        }
        log.info("%d playlists carregadas de %s", len(self._playlists), self.path)

    def save(self) -> None:
        save_json(self.path, self._playlists)

    def all(self) -> dict[str, list[str]]:
        return {name: list(items) for name, items in self._playlists.items()}

    def get(self, name: str) -> list[str]:
        name = normalize_name(name)
        if name not in self._playlists:
            raise UserError(f"❌ A playlist `{name}` não existe! Use `/criar_playlist` para criar.")
        return list(self._playlists[name])

    def create(self, name: str) -> str:
        name = normalize_name(name)
        if not name or len(name) > MAX_NAME_LENGTH:
            raise UserError(
                f"❌ O nome da playlist deve ter entre 1 e {MAX_NAME_LENGTH} caracteres."
            )
        if name in self._playlists:
            raise UserError(f"❌ A playlist `{name}` já existe!")
        self._playlists[name] = []
        self.save()
        return name

    def delete(self, name: str) -> None:
        self.get(name)
        del self._playlists[normalize_name(name)]
        self.save()

    def add(self, name: str, audio: str) -> None:
        items = self.get(name)
        audio = normalize_name(audio)
        if audio in items:
            raise UserError(f"❌ O áudio `{audio}` já está na playlist `{normalize_name(name)}`.")
        self._playlists[normalize_name(name)].append(audio)
        self.save()

    def remove(self, name: str, audio: str) -> None:
        items = self.get(name)
        audio = normalize_name(audio)
        if audio not in items:
            raise UserError(f"❌ O áudio `{audio}` não está na playlist `{normalize_name(name)}`.")
        self._playlists[normalize_name(name)].remove(audio)
        self.save()

    def remove_everywhere(self, audio: str) -> None:
        """Tira um áudio apagado de todas as playlists."""
        audio = normalize_name(audio)
        changed = False
        for items in self._playlists.values():
            if audio in items:
                items[:] = [i for i in items if i != audio]
                changed = True
        if changed:
            self.save()
