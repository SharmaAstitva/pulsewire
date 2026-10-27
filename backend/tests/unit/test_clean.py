from datetime import datetime

import feedparser

from pipeline.clean import clean_text, extract_image, normalize_url, parse_date, split_sentences, url_hash


def test_clean_text_strips_html_and_boilerplate():
    raw = "<p>Hello <b>world</b> &amp; friends.</p> The post Hello appeared first on Example."
    assert clean_text(raw) == "Hello world & friends."


def test_clean_text_truncates_on_word_boundary():
    text = clean_text("word " * 100, max_chars=22)
    assert text.endswith("…") and len(text) <= 23


def test_normalize_url_removes_tracking_and_trailing_slash():
    a = normalize_url("HTTPS://Example.com/story/?utm_source=x&id=7#top")
    b = normalize_url("https://example.com/story?id=7")
    assert a == b
    assert url_hash("https://example.com/s?utm_medium=rss") == url_hash("https://example.com/s")


def test_parse_date_handles_missing_and_future_dates():
    now = datetime(2026, 10, 24, 12)
    assert parse_date({}, now=now) == now
    future = feedparser.parse("<rss><channel><item><title>x</title>"
                              "<pubDate>Mon, 01 Jan 2035 00:00:00 GMT</pubDate></item></channel></rss>")
    assert parse_date(future.entries[0], now=now) == now


def test_extract_image_from_media_and_html(tmp_path):
    from tests.conftest import FIXTURES
    feed = feedparser.parse((FIXTURES / "sample_feed.xml").read_bytes())
    assert extract_image(feed.entries[0]) == "https://example.com/img/nvidia.jpg"
    assert extract_image(feed.entries[1]) == "https://example.com/img/floods.jpg"
    assert extract_image(feed.entries[2]) is None


def test_split_sentences():
    assert split_sentences("One thing. Two things! 3 more?") == ["One thing.", "Two things!", "3 more?"]
