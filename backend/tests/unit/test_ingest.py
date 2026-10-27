import json

import pytest

from pipeline.ingest import fetch_all, load_feeds, parse_feed

SOURCE = {"name": "Unit Feed", "url": "https://unit.test/rss", "authority": 0.7}


def rss(items: str) -> str:
    return f"<?xml version='1.0'?><rss version='2.0'><channel><title>t</title>{items}</channel></rss>"


def test_parse_feed_extracts_fields():
    xml = rss("""<item><title>Parliament passes the new data protection bill</title>
        <link>https://unit.test/a</link><author>Jane Doe</author>
        <description>&lt;p&gt;The bill passed on Monday.&lt;/p&gt;</description>
        <pubDate>Sat, 24 Oct 2026 10:00:00 GMT</pubDate></item>""")
    [article] = parse_feed(xml, SOURCE)
    assert article.title == "Parliament passes the new data protection bill"
    assert article.content == "The bill passed on Monday."
    assert article.author == "Jane Doe"
    assert article.source == "Unit Feed" and article.source_authority == 0.7
    assert len(article.url_hash) == 64


def test_parse_feed_prefers_full_content_over_summary():
    xml = """<?xml version='1.0'?><feed xmlns='http://www.w3.org/2005/Atom'>
      <entry><title>Atom entry with both summary and content</title>
      <link href='https://unit.test/atom'/><summary>Short teaser.</summary>
      <content type='html'>Full article body text.</content>
      <updated>2026-10-24T10:00:00Z</updated></entry></feed>"""
    [article] = parse_feed(xml, SOURCE)
    assert article.content == "Full article body text."


def test_parse_feed_skips_entries_without_link_or_real_title():
    xml = rss("""<item><title>No link here but a long enough title</title></item>
                 <item><title>Bad</title><link>https://unit.test/short</link></item>
                 <item><title>Relative link is also rejected entirely</title><link>/relative</link></item>""")
    assert parse_feed(xml, SOURCE) == []


def test_parse_feed_respects_max_items():
    items = "".join(
        f"<item><title>Headline number {i} for the cap test</title><link>https://unit.test/{i}</link></item>"
        for i in range(10)
    )
    assert len(parse_feed(rss(items), SOURCE, max_items=3)) == 3


def test_parse_feed_rejects_garbage():
    with pytest.raises(ValueError):
        parse_feed(b"this is not xml at all <<<", SOURCE)


def test_load_feeds_skips_inactive(tmp_path):
    path = tmp_path / "feeds.json"
    path.write_text(json.dumps([
        {"name": "On", "url": "https://a"},
        {"name": "Off", "url": "https://b", "active": False},
    ]))
    assert [f["name"] for f in load_feeds(path)] == ["On"]


def test_fetch_all_isolates_failures():
    good = rss("<item><title>A perfectly normal headline</title><link>https://unit.test/ok</link></item>")

    def fetcher(url):
        if "bad" in url:
            raise TimeoutError("too slow")
        return good

    results = fetch_all([{"name": "Good", "url": "https://good"}, {"name": "Bad", "url": "https://bad"}],
                        fetcher=fetcher)
    by_name = {r.source["name"]: r for r in results}
    assert len(by_name["Good"].articles) == 1 and by_name["Good"].error is None
    assert by_name["Bad"].articles == [] and "too slow" in by_name["Bad"].error
