import pytest

from cazalberto.audio.wow import WowCatalog


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")
    return path


@pytest.fixture
def catalog(tmp_path):
    root = tmp_path / "wow-ost"
    _touch(root / "1.0 Classic" / "1. Legends of Azeroth.mp3")
    _touch(root / "1.0 Classic" / "2. Darnassus.mp3")
    _touch(root / "1.0 Classic" / "10. Forest (Elwynn Forest).mp3")
    _touch(root / "1.0 Classic" / "capa.jpg")
    _touch(root / "7.0 Legion" / "10. Dalaran (Jaina).mp3")
    _touch(root / "7.1 Return to Karazhan" / "1. Karazhan.mp3")
    _touch(root / "11.0 The War Within" / "1. Dornogal.mp3")
    _touch(root / "11.0.7 Siren Isle" / "1. Siren Isle.mp3")
    _touch(root / "11.1 Undermine(D)" / "1. Undermine.mp3")
    _touch(root / "Pasta Qualquer" / "x.mp3")
    c = WowCatalog(root)
    c.scan()
    return c


def test_scan_builds_names_in_track_order(catalog):
    assert catalog.list("classic")[1] == [
        "classic-legends-of-azeroth",
        "classic-darnassus",
        "classic-forest-elwynn-forest",
    ]
    assert len(catalog) == 8  # ignora capa.jpg e a pasta desconhecida


def test_resolve_exact_and_fragment(catalog, tmp_path):
    root = tmp_path / "wow-ost"
    assert catalog.resolve("classic-darnassus") == root / "1.0 Classic" / "2. Darnassus.mp3"
    assert catalog.resolve("classic-elwynn").name == "10. Forest (Elwynn Forest).mp3"
    # Fragmento pela expansão inteira encontra também os patches (7.1 faz parte de Legion).
    assert catalog.resolve("legion-karazhan").name == "1. Karazhan.mp3"
    assert catalog.resolve("classic-nada") is None
    assert catalog.resolve("quico") is None


def test_versions_are_matched_exactly(catalog):
    assert catalog.list("siren")[1] == ["siren-siren-isle"]
    assert catalog.list("tww")[1] == ["tww-dornogal", "siren-siren-isle"]
    assert catalog.list("undermine")[1] == ["undermine-undermine"]


def test_aliases(catalog):
    assert catalog.list("0")[0] == "World of Warcraft: Classic"
    assert catalog.list("vanilla")[1] == catalog.list("classic")[1]
    assert catalog.list("kara")[1] == ["kara-karazhan"]
    assert catalog.list("xyz") is None


def test_simple_layout(tmp_path):
    _touch(tmp_path / "classic" / "Stormwind.mp3")
    _touch(tmp_path / "shadowlands" / "Oribos.mp3")
    c = WowCatalog(tmp_path)
    c.scan()
    assert c.names() == ["classic-stormwind", "sl-oribos"]


def test_duplicate_titles_get_suffix(tmp_path):
    _touch(tmp_path / "1.0 Classic" / "1. Naxxramas.mp3")
    _touch(tmp_path / "1.0 Classic" / "2. Naxxramas!.mp3")
    c = WowCatalog(tmp_path)
    c.scan()
    assert c.names() == ["classic-naxxramas", "classic-naxxramas-2"]


def test_disabled_without_folder(tmp_path):
    c = WowCatalog(tmp_path / "nao-existe")
    c.scan()
    assert not c.enabled
    assert c.resolve("classic-x") is None
