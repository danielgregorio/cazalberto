import json

import pytest

from cazalberto.errors import UserError
from cazalberto.playlists import PlaylistStore


@pytest.fixture
def store(tmp_path):
    s = PlaylistStore(tmp_path / "playlists.json")
    s.load()
    return s


def test_legacy_empty_format_is_ignored(tmp_path):
    path = tmp_path / "playlists.json"
    path.write_text('{"playlists": []}', encoding="utf-8")
    store = PlaylistStore(path)
    store.load()
    assert store.all() == {}


def test_create_add_remove_delete(store):
    store.create("Rock")
    store.add("rock", "Numb")
    store.add("rock", "linkinpark")
    assert store.get("ROCK") == ["numb", "linkinpark"]

    with pytest.raises(UserError):
        store.add("rock", "numb")

    store.remove("rock", "numb")
    assert store.get("rock") == ["linkinpark"]
    assert json.loads(store.path.read_text(encoding="utf-8")) == {"rock": ["linkinpark"]}

    store.delete("rock")
    assert store.all() == {}


def test_errors(store):
    with pytest.raises(UserError):
        store.get("nada")
    with pytest.raises(UserError):
        store.create("x" * 40)
    store.create("a")
    with pytest.raises(UserError):
        store.create("A")


def test_remove_everywhere(store):
    store.create("a")
    store.create("b")
    store.add("a", "x")
    store.add("b", "x")
    store.add("b", "y")
    store.remove_everywhere("x")
    assert store.all() == {"a": [], "b": ["y"]}
