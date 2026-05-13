import pytest

from app.services.rss_fetcher import _entry_matches_filters, _parse_feed, ingest_new_entries


def test_parse_feed_basic() -> None:
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel><title>Test Feed</title>
    <item><title>Article 1</title><link>https://example.com/1</link>
    <guid>guid-1</guid><description>Test description</description></item>
    <item><title>Article 2</title><link>https://example.com/2</link>
    <guid>guid-2</guid></item>
    </channel></rss>"""

    feed = _parse_feed(sample_xml, "https://example.com/feed")
    assert len(feed.entries) == 2
    assert feed.entries[0]["title"] == "Article 1"
    assert feed.entries[1]["link"] == "https://example.com/2"


def test_parse_feed_empty() -> None:
    feed = _parse_feed("", "https://example.com/feed")
    assert len(feed.entries) == 0


def test_parse_feed_invalid_xml() -> None:
    feed = _parse_feed("this is not xml at all", "https://example.com/feed")
    assert len(feed.entries) == 0


def test_parse_feed_atom() -> None:
    atom_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <title>Atom Feed</title>
      <entry><title>Atom Entry</title>
      <id>atom-id-1</id>
      <link href="https://example.com/atom1"/></entry>
    </feed>"""
    feed = _parse_feed(atom_xml, "https://example.com/atom")
    assert len(feed.entries) == 1
    assert feed.entries[0]["title"] == "Atom Entry"


def test_entry_matches_filters_no_filters() -> None:
    entry = {"title": "Test Article", "summary": "Some content"}
    assert _entry_matches_filters(entry, None, None, None) is True


def test_entry_matches_filters_keyword_match() -> None:
    entry = {"title": "XSS 攻击防护", "summary": "Web 安全"}
    assert _entry_matches_filters(entry, ["xss"], None, None) is True
    assert _entry_matches_filters(entry, ["sql注入"], None, None) is False


def test_entry_matches_filters_author() -> None:
    entry = {"title": "Test", "authors": [{"name": "Alice"}]}
    assert _entry_matches_filters(entry, None, ["Alice"], None) is True
    assert _entry_matches_filters(entry, None, ["Bob"], None) is False


def test_entry_matches_filters_category() -> None:
    entry = {"title": "Test", "tags": [{"term": "Security"}, {"term": "Web"}]}
    assert _entry_matches_filters(entry, None, None, ["security"]) is True
    assert _entry_matches_filters(entry, None, None, ["crypto"]) is False


def test_entry_matches_filters_combined() -> None:
    entry = {
        "title": "SQL Injection Defense",
        "summary": "How to prevent SQL injection",
        "authors": [{"name": "Charlie"}],
    }
    assert _entry_matches_filters(entry, ["sql"], ["Charlie"], None) is True
    assert _entry_matches_filters(entry, ["sql"], ["Dave"], None) is False


def test_entry_matches_filters_empty_authors_list() -> None:
    entry = {"title": "Test", "authors": []}
    assert _entry_matches_filters(entry, None, ["Alice"], None) is False


def test_entry_matches_filters_non_dict_authors() -> None:
    entry = {"title": "Test", "authors": ["plain-string"]}
    assert _entry_matches_filters(entry, None, ["Alice"], None) is False


def test_entry_matches_filters_non_dict_tags() -> None:
    entry = {"title": "Test", "tags": ["plain-string"]}
    assert _entry_matches_filters(entry, None, None, ["security"]) is False


def test_entry_matches_filters_missing_fields() -> None:
    entry = {}
    assert _entry_matches_filters(entry, ["keyword"], None, None) is False
    assert _entry_matches_filters(entry, None, None, None) is True


def test_entry_matches_filters_case_insensitive_keyword() -> None:
    entry = {"title": "XSS ATTACK PREVENTION", "summary": ""}
    assert _entry_matches_filters(entry, ["xss"], None, None) is True
    assert _entry_matches_filters(entry, ["attack"], None, None) is True


@pytest.mark.asyncio
async def test_ingest_new_entries_no_kb() -> None:
    """ingest_new_entries returns 0 when kb doesn't exist."""
    result = await ingest_new_entries("nonexistent-feed", "nonexistent-kb")
    assert result == 0
