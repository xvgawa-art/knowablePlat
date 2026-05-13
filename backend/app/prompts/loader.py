"""Prompt loader — reads prompt templates from .md files in this directory."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent

_cache: dict[str, str] = {}


def load_prompt(name: str) -> str:
    """Load a prompt template by filename (without .md extension). Results are cached."""
    if name not in _cache:
        path = PROMPTS_DIR / f"{name}.md"
        _cache[name] = path.read_text(encoding="utf-8").strip()
    return _cache[name]
