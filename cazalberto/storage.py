"""Persistência em JSON com escrita atômica."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


def load_json(path: Path, default: Any) -> Any:
    """Lê um JSON. Se não existir, devolve `default`; se estiver corrompido,
    guarda uma cópia `.corrupted` e devolve `default` em vez de perder o arquivo."""
    if not path.exists():
        return default
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        backup = path.with_suffix(path.suffix + ".corrupted")
        log.error("Arquivo %s corrompido (%s). Cópia salva em %s", path, exc, backup)
        path.replace(backup)
        return default


def save_json(path: Path, data: Any) -> None:
    """Grava o JSON num arquivo temporário e troca de uma vez, pra nunca
    deixar o arquivo pela metade se o bot cair no meio da escrita."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
