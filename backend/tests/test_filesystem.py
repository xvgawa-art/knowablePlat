import pytest

import app.services.filesystem as fs_mod
from app.services.filesystem import delete_wiki_page, save_raw_content, save_wiki_index, save_wiki_log, save_wiki_page


@pytest.fixture
def tmp_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(fs_mod, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(fs_mod, "WIKI_DIR", tmp_path / "wiki")
    return tmp_path


def test_save_raw_content(tmp_dirs):
    path = save_raw_content("test-kb", "src-001", "# Hello")
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "# Hello"
    assert path.parent.name == "test-kb"
    assert path.name == "src-001.md"


def test_save_raw_content_overwrite(tmp_dirs):
    save_raw_content("test-kb", "src-001", "v1")
    path = save_raw_content("test-kb", "src-001", "v2")
    assert path.read_text(encoding="utf-8") == "v2"


def test_save_raw_content_different_kb(tmp_dirs):
    p1 = save_raw_content("kb-a", "s1", "a")
    p2 = save_raw_content("kb-b", "s1", "b")
    assert p1.read_text(encoding="utf-8") == "a"
    assert p2.read_text(encoding="utf-8") == "b"


def test_save_wiki_page(tmp_dirs):
    path = save_wiki_page("test-kb", "my-page", "# Wiki Content")
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "# Wiki Content"
    assert path.parent.name == "test-kb"
    assert path.name == "my-page.md"


def test_save_wiki_index(tmp_dirs):
    path = save_wiki_index("test-kb", "# Index\n- [[page-1]]")
    assert path.exists()
    assert path.name == "index.md"
    assert "page-1" in path.read_text(encoding="utf-8")


def test_save_wiki_log_append(tmp_dirs):
    save_wiki_log("test-kb", "## [2026-05-14] ingest | Article 1")
    save_wiki_log("test-kb", "## [2026-05-14] ingest | Article 2")
    log_path = tmp_dirs / "wiki" / "test-kb" / "log.md"
    content = log_path.read_text(encoding="utf-8")
    assert "Article 1" in content
    assert "Article 2" in content
    assert content.count("\n") == 2


def test_save_wiki_log_creates_dir(tmp_dirs):
    save_wiki_log("new-kb", "first entry")
    log_path = tmp_dirs / "wiki" / "new-kb" / "log.md"
    assert log_path.exists()


def test_delete_wiki_page(tmp_dirs):
    save_wiki_page("test-kb", "doomed", "bye")
    path = tmp_dirs / "wiki" / "test-kb" / "doomed.md"
    assert path.exists()
    delete_wiki_page("test-kb", "doomed")
    assert not path.exists()


def test_delete_wiki_page_missing_noop(tmp_dirs):
    delete_wiki_page("test-kb", "nonexistent")
