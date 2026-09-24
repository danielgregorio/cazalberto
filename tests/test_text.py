from cazalberto.text import chunk_lines, normalize_name, slugify, truncate


def test_slugify():
    assert slugify("Dalaran (Jaina)") == "dalaran-jaina"
    assert slugify("Ruins of Ahn'Qiraj") == "ruins-of-ahnqiraj"
    assert slugify("Não Compensa!") == "nao-compensa"


def test_normalize_name():
    assert normalize_name("  Ai   Chaves ") == "ai chaves"


def test_truncate():
    assert truncate("abc", 5) == "abc"
    assert truncate("abcdefgh", 5) == "abcd…"


def test_chunk_lines_respects_limit():
    text = "\n".join(f"linha {i}" for i in range(500))
    chunks = chunk_lines(text, limit=100)
    assert all(len(c) <= 100 for c in chunks)
    assert "\n".join(chunks) == text


def test_chunk_lines_splits_huge_line():
    chunks = chunk_lines("x" * 250, limit=100)
    assert [len(c) for c in chunks] == [100, 100, 50]
