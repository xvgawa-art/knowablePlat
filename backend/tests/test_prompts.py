import pytest

from app.prompts.loader import load_prompt


def test_load_prompt_returns_content():
    result = load_prompt("ingest_extract")
    assert "知识提取" in result
    assert "JSON" in result


def test_load_prompt_caches():
    a = load_prompt("query_answer")
    b = load_prompt("query_answer")
    assert a is b


def test_load_prompt_all_files():
    prompts = [
        "ingest_extract",
        "ingest_synthesize",
        "ingest_crossref",
        "query_answer",
        "generate_outline",
        "generate_section",
        "generate_integrate",
        "lint_contradictions",
        "ingest_notify",
        "tool_extract",
        "tool_recommend",
        "tool_categorize",
    ]
    for name in prompts:
        content = load_prompt(name)
        assert len(content) > 20, f"Prompt {name} is too short"


def test_load_prompt_missing_file():
    with pytest.raises(FileNotFoundError):
        load_prompt("nonexistent_prompt")
