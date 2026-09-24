"""Catálogo das trilhas sonoras de World of Warcraft.

As músicas são descobertas lendo a pasta configurada em WOW_OST_DIR, em vez de
ficarem listadas uma a uma (com caminho absoluto) no commands.json.

Estrutura esperada (os nomes das pastas só precisam começar pela versão):

    wow-ost/
        1.0 Classic/1. Legends of Azeroth.mp3
        7.1 Return to Karazhan/...
        11.1 Undermine(D)/...

Cada música vira um comando `<prefixo>-<nome>`, ex.: `classic-legends-of-azeroth`.
Também dá para usar pastas com o próprio prefixo como nome (`wow-music/classic/`).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from ..text import slugify

log = logging.getLogger(__name__)

AUDIO_EXTENSIONS = {".mp3", ".ogg", ".flac", ".wav", ".m4a"}
TRACK_NUMBER = re.compile(r"^\d+\s*[.\-_)]\s*")


@dataclass(frozen=True)
class Section:
    """Uma pasta da trilha sonora (um patch ou expansão)."""

    prefix: str
    version: str
    expansion: str


@dataclass(frozen=True)
class Expansion:
    key: str
    title: str
    aliases: tuple[str, ...]


EXPANSIONS: tuple[Expansion, ...] = (
    Expansion("classic", "World of Warcraft: Classic", ("0", "vanilla")),
    Expansion("tbc", "The Burning Crusade", ("1", "burning", "crusade")),
    Expansion("wotlk", "Wrath of the Lich King", ("2", "lich", "wrath")),
    Expansion("cata", "Cataclysm", ("3", "cataclysm")),
    Expansion("mop", "Mists of Pandaria", ("4", "mists", "pandaria")),
    Expansion("wod", "Warlords of Draenor", ("5", "draenor", "warlords")),
    Expansion("legion", "Legion", ("6",)),
    Expansion("bfa", "Battle for Azeroth", ("7", "battle", "azeroth")),
    Expansion("sl", "Shadowlands", ("8", "shadowlands")),
    Expansion("df", "Dragonflight", ("9", "dragonflight")),
    Expansion("tww", "The War Within", ("10", "war", "within")),
    Expansion("undermine", "Undermine", ("11",)),
)

SECTIONS: tuple[Section, ...] = (
    Section("classic", "1.0", "classic"),
    Section("tbc", "2.0", "tbc"),
    Section("wotlk", "3.0", "wotlk"),
    Section("cata", "4.0", "cata"),
    Section("mop", "5.0", "mop"),
    Section("wod", "6.0", "wod"),
    Section("legion", "7.0", "legion"),
    Section("kara", "7.1", "legion"),
    Section("tomb", "7.2", "legion"),
    Section("argus", "7.3", "legion"),
    Section("bfa", "8.0", "bfa"),
    Section("tides", "8.1", "bfa"),
    Section("azshara", "8.2", "bfa"),
    Section("nzoth", "8.3", "bfa"),
    Section("sl", "9.0", "sl"),
    Section("chains", "9.1", "sl"),
    Section("eternity", "9.2", "sl"),
    Section("df", "10.0", "df"),
    Section("embers", "10.1", "df"),
    Section("dream", "10.2", "df"),
    Section("tww", "11.0", "tww"),
    Section("siren", "11.0.7", "tww"),
    Section("undermine", "11.1", "undermine"),
)

_EXPANSION_BY_KEY = {e.key: e for e in EXPANSIONS}
# Nomes alternativos de pasta usados no layout simplificado (wow-music/<nome>/).
_FOLDER_ALIASES = {"shadowlands": "sl", "dragonflight": "df"}


def _track_title(filename: str) -> str:
    return TRACK_NUMBER.sub("", Path(filename).stem)


def _natural_key(path: Path) -> tuple:
    match = re.match(r"^(\d+)", path.name)
    return (int(match.group(1)) if match else float("inf"), path.name.lower())


class WowCatalog:
    def __init__(self, root: Path | None) -> None:
        self.root = root
        self._tracks: dict[str, Path] = {}
        self._by_section: dict[str, list[str]] = {}

    @property
    def enabled(self) -> bool:
        return bool(self._tracks)

    def __len__(self) -> int:
        return len(self._tracks)

    def names(self) -> list[str]:
        return list(self._tracks)

    def _match_section(self, folder: Path) -> Section | None:
        name = folder.name.lower()
        name = _FOLDER_ALIASES.get(name, name)
        version = folder.name.split(" ", 1)[0]
        for section in SECTIONS:
            if version == section.version or name == section.prefix:
                return section
        return None

    def scan(self) -> None:
        self._tracks.clear()
        self._by_section.clear()
        if self.root is None or not self.root.is_dir():
            log.info("Trilhas do WoW desativadas (pasta não configurada ou inexistente).")
            return

        for folder in sorted(p for p in self.root.iterdir() if p.is_dir()):
            section = self._match_section(folder)
            if section is None:
                log.warning("Pasta do WoW não reconhecida, ignorando: %s", folder.name)
                continue
            files = sorted(
                (f for f in folder.iterdir() if f.suffix.lower() in AUDIO_EXTENSIONS),
                key=_natural_key,
            )
            names = self._by_section.setdefault(section.prefix, [])
            for file in files:
                base = f"{section.prefix}-{slugify(_track_title(file.name)) or 'faixa'}"
                name, counter = base, 2
                while name in self._tracks:
                    name = f"{base}-{counter}"
                    counter += 1
                self._tracks[name] = file
                names.append(name)

        log.info("%d trilhas do WoW encontradas em %s", len(self._tracks), self.root)

    def resolve(self, command: str) -> Path | None:
        """Acha a música pelo nome exato ou, se não houver, por um trecho do nome
        (`classic-elwynn` encontra `classic-forest-elwynn-forest`)."""
        command = slugify(command)
        if command in self._tracks:
            return self._tracks[command]

        prefix, _, fragment = command.partition("-")
        prefixes = self._prefixes_for(prefix)
        if not prefixes or not fragment:
            return None
        for section_prefix in prefixes:
            for name in self._by_section.get(section_prefix, []):
                if fragment in name[len(section_prefix) + 1 :]:
                    return self._tracks[name]
        return None

    def _prefixes_for(self, key: str) -> list[str]:
        expansion = self.find_expansion(key)
        if expansion is not None:
            return [s.prefix for s in SECTIONS if s.expansion == expansion.key]
        if any(s.prefix == key for s in SECTIONS):
            return [key]
        return []

    @staticmethod
    def find_expansion(key: str) -> Expansion | None:
        key = key.lower().strip()
        if key in _EXPANSION_BY_KEY:
            return _EXPANSION_BY_KEY[key]
        for expansion in EXPANSIONS:
            if key in expansion.aliases:
                return expansion
        return None

    def list(self, key: str) -> tuple[str, list[str]] | None:
        """Lista as músicas de uma expansão (ou de uma seção específica, como `kara`).
        Devolve (título, nomes) ou None se a chave não for reconhecida."""
        key = key.lower().strip()
        expansion = self.find_expansion(key)
        if expansion is not None:
            names = [
                name
                for section in SECTIONS
                if section.expansion == expansion.key
                for name in self._by_section.get(section.prefix, [])
            ]
            return expansion.title, names
        for section in SECTIONS:
            if section.prefix == key:
                title = _EXPANSION_BY_KEY[section.expansion].title
                return f"{title} ({section.version})", list(self._by_section.get(key, []))
        return None
