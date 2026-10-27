"""Stage 1: fetch RSS feeds concurrently and parse them into RawArticle records."""
import json
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import feedparser
import httpx

from pipeline.clean import clean_text, clean_title, extract_image, parse_date, strip_html, url_hash

log = logging.getLogger("pulsewire.ingest")

USER_AGENT = "PulseWireBot/1.0 (+https://github.com/SharmaAstitva/pulsewire)"
Fetcher = Callable[[str], bytes]


@dataclass
class RawArticle:
    url: str
    url_hash: str
    title: str
    content: str
    image_url: str | None
    author: str | None
    published_at: datetime
    source: str
    source_authority: float = 0.5


@dataclass
class FeedResult:
    source: dict
    articles: list[RawArticle] = field(default_factory=list)
    error: str | None = None


def load_feeds(path: Path) -> list[dict]:
    feeds = json.loads(Path(path).read_text(encoding="utf-8"))
    return [f for f in feeds if f.get("active", True)]


def http_fetch(url: str) -> bytes:
    response = httpx.get(url, timeout=20, follow_redirects=True, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.content


def parse_feed(raw: bytes | str, source: dict, max_items: int = 15) -> list[RawArticle]:
    feed = feedparser.parse(raw)
    if feed.bozo and not feed.entries:
        raise ValueError(f"Unreadable feed: {feed.bozo_exception}")

    articles = []
    for entry in feed.entries[:max_items]:
        url = (entry.get("link") or "").strip()
        title = clean_title(entry.get("title"), source["name"])
        if not url.startswith("http") or len(title) < 10:
            continue
        body = entry["content"][0].get("value", "") if entry.get("content") else ""
        content = clean_text(body or entry.get("summary") or entry.get("description"))
        articles.append(
            RawArticle(
                url=url,
                url_hash=url_hash(url),
                title=title[:500],
                content=content,
                image_url=extract_image(entry),
                author=strip_html(entry.get("author"))[:300] or None,
                published_at=parse_date(entry),
                source=source["name"],
                source_authority=float(source.get("authority", 0.5)),
            )
        )
    return articles


def fetch_all(feeds: list[dict], max_items: int = 15, fetcher: Fetcher = http_fetch,
              workers: int = 8) -> list[FeedResult]:
    """Fetch every feed in parallel. One broken feed never stops the run."""

    def work(source: dict) -> FeedResult:
        try:
            return FeedResult(source, parse_feed(fetcher(source["url"]), source, max_items))
        except Exception as exc:
            log.warning("Feed failed: %s (%s)", source["name"], exc)
            return FeedResult(source, error=str(exc)[:500])

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(work, feeds))
