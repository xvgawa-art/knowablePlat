"""Filesystem persistence for raw content and wiki pages."""

from pathlib import Path

import structlog

from app.config import RAW_DIR, WIKI_DIR

logger = structlog.get_logger()


def save_raw_content(kb_slug: str, source_id: str, content: str) -> Path:
    """Save raw fetched content to raw/{kb_slug}/{source_id}.md."""
    raw_dir = RAW_DIR / kb_slug
    raw_dir.mkdir(parents=True, exist_ok=True)
    filepath = raw_dir / f"{source_id}.md"
    filepath.write_text(content, encoding="utf-8")
    logger.info("raw_saved", kb_slug=kb_slug, source_id=source_id, path=str(filepath))
    return filepath


def save_wiki_page(kb_slug: str, slug: str, content: str) -> Path:
    """Save wiki page content to wiki/{kb_slug}/{slug}.md."""
    wiki_dir = WIKI_DIR / kb_slug
    wiki_dir.mkdir(parents=True, exist_ok=True)
    filepath = wiki_dir / f"{slug}.md"
    filepath.write_text(content, encoding="utf-8")
    logger.info("wiki_page_saved", kb_slug=kb_slug, slug=slug, path=str(filepath))
    return filepath


def save_wiki_index(kb_slug: str, content: str) -> Path:
    """Save wiki index to wiki/{kb_slug}/index.md."""
    wiki_dir = WIKI_DIR / kb_slug
    wiki_dir.mkdir(parents=True, exist_ok=True)
    filepath = wiki_dir / "index.md"
    filepath.write_text(content, encoding="utf-8")
    return filepath


def save_wiki_log(kb_slug: str, entry: str) -> None:
    """Append an entry to wiki/{kb_slug}/log.md."""
    wiki_dir = WIKI_DIR / kb_slug
    wiki_dir.mkdir(parents=True, exist_ok=True)
    filepath = wiki_dir / "log.md"
    with filepath.open("a", encoding="utf-8") as f:
        f.write(entry + "\n")


def delete_wiki_page(kb_slug: str, slug: str) -> None:
    """Delete a wiki page file from disk."""
    filepath = WIKI_DIR / kb_slug / f"{slug}.md"
    if filepath.exists():
        filepath.unlink()
        logger.info("wiki_page_deleted", kb_slug=kb_slug, slug=slug)
