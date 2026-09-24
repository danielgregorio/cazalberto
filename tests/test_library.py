import json

import pytest

from cazalberto.audio.library import AudioLibrary
from cazalberto.errors import UserError


@pytest.fixture
def library(tmp_path):
    audio_dir = tmp_path / "audio_clips"
    audio_dir.mkdir()
    lib = AudioLibrary(tmp_path / "data" / "commands.json", audio_dir)
    lib.load()
    return lib


def test_migrates_windows_paths(tmp_path):
    commands = tmp_path / "commands.json"
    commands.write_text(
        json.dumps({"quico": "audio_clips\\quico.mp3", "Ai Chaves": "audio_clips\\ai chaves.mp3"}),
        encoding="utf-8",
    )
    lib = AudioLibrary(commands, tmp_path / "clips")
    lib.load()

    assert lib.resolve("quico") == tmp_path / "clips" / "quico.mp3"
    assert lib.resolve("ai chaves") == tmp_path / "clips" / "ai chaves.mp3"
    saved = json.loads(commands.read_text(encoding="utf-8"))
    assert saved == {"ai chaves": "ai chaves.mp3", "quico": "quico.mp3"}


def test_absolute_paths_are_kept(tmp_path):
    commands = tmp_path / "commands.json"
    commands.write_text(json.dumps({"x": "D:\\music\\x.mp3"}), encoding="utf-8")
    lib = AudioLibrary(commands, tmp_path)
    lib.load()
    assert json.loads(commands.read_text(encoding="utf-8")) == {"x": "D:\\music\\x.mp3"}


def test_add_resolve_and_remove(library):
    path = library.target_path("Meu Áudio")
    assert path.parent == library.audio_dir
    assert path.name == "meu-audio.mp3"
    path.write_bytes(b"x")

    library.add("Meu Áudio", path)
    assert "meu áudio" in library
    assert library.resolve("MEU ÁUDIO") == path
    assert json.loads(library.commands_file.read_text(encoding="utf-8")) == {
        "meu áudio": "meu-audio.mp3"
    }

    assert library.remove("meu áudio") == path
    assert "meu áudio" not in library


def test_add_duplicate_fails(library):
    library.add("a", library.audio_dir / "a.mp3")
    with pytest.raises(UserError):
        library.add("A", library.audio_dir / "a.mp3")


@pytest.mark.parametrize("name", ["", "../../etc/passwd", "a" * 33, "nome/com/barra"])
def test_invalid_names(library, name):
    with pytest.raises(UserError):
        library.validate_name(name)


def test_target_path_never_leaves_audio_dir(library):
    assert library.target_path("..").parent == library.audio_dir
    (library.audio_dir / "x.mp3").write_bytes(b"")
    assert library.target_path("x").name == "x-2.mp3"


def test_remove_does_not_return_files_outside_audio_dir(library, tmp_path):
    outside = tmp_path / "fora.mp3"
    library.add("fora", outside)
    assert library.remove("fora") is None


def test_remove_keeps_shared_file(library):
    path = library.audio_dir / "a.mp3"
    library.add("a", path)
    library.add("b", path)
    assert library.remove("a") is None


def test_remove_missing_fails(library):
    with pytest.raises(UserError):
        library.remove("nada")
