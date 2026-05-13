from app.services.rss_fetcher import _entry_matches_filters, _parse_feed


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
