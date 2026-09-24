import json

from cazalberto.storage import load_json, save_json


def test_load_missing_returns_default(tmp_path):
    assert load_json(tmp_path / "nope.json", {"a": 1}) == {"a": 1}


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "sub" / "data.json"
    save_json(path, {"não": "ç"})
    assert load_json(path, {}) == {"não": "ç"}
    assert "não" in path.read_text(encoding="utf-8")  # ensure_ascii=False
    assert not list(path.parent.glob("*.tmp"))


def test_corrupted_file_is_preserved(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("{quebrado", encoding="utf-8")
    assert load_json(path, {}) == {}
    assert (tmp_path / "data.json.corrupted").read_text(encoding="utf-8") == "{quebrado"
    json.dumps({})  # sanity
