"""Text cleaning and normalisation helpers. Pure functions, easy to test."""
import calendar
import hashlib
import html
import re
from datetime import UTC, datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from bs4 import BeautifulSoup

_BOILERPLATE = [
    re.compile(r"The post .{0,200}? appeared first on .{0,200}?\.?$", re.I),
    re.compile(r"Continue reading\.{0,3}\s*$", re.I),
    re.compile(r"Read more\.{0,3}\s*$", re.I),
    re.compile(r"\[(?:…|\.\.\.|&#8230;)\]"),
    re.compile(r"Comments?\s*$", re.I),
]
_TRACKING_PARAMS = ("utm_", "fbclid", "gclid", "ocid", "cmpid", "at_medium", "at_campaign")


def strip_html(raw: str | None) -> str:
    if not raw:
        return ""
    text = BeautifulSoup(raw, "html.parser").get_text(" ")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def clean_text(raw: str | None, max_chars: int = 2000) -> str:
    text = strip_html(raw)
    for pattern in _BOILERPLATE:
        text = pattern.sub("", text).strip()
    if len(text) > max_chars:
        cut = text[:max_chars]
        text = cut[: cut.rfind(" ")] + "…" if " " in cut else cut
    return text


_TITLE_SUFFIX = re.compile(r"^(?P<head>.+?)\s+[-–—|]\s+(?P<tail>[^-–—|]+)$")


def clean_title(raw: str | None, source: str) -> str:
    """Strip HTML and a trailing publisher name ("... - BBC News", "... | BBC")."""
    title = strip_html(raw)
    match = _TITLE_SUFFIX.match(title)
    if match:
        tail = match["tail"].strip().lower()
        name = source.strip().lower()
        if tail == name or name.startswith(tail + " "):
            return match["head"].strip()
    return title


def normalize_url(url: str) -> str:
    """Canonical form used for duplicate detection."""
    parts = urlsplit(url.strip())
    query = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not k.lower().startswith(_TRACKING_PARAMS)
    ]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def url_hash(url: str) -> str:
    return hashlib.sha256(normalize_url(url).encode()).hexdigest()


def parse_date(entry, now: datetime | None = None) -> datetime:
    """Return a naive UTC datetime. Falls back to `now` when the feed has no date,
    and clamps future dates (some feeds publish with wrong time zones)."""
    now = now or datetime.now(UTC).replace(tzinfo=None)
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = entry.get(key)
        if parsed:
            value = datetime.fromtimestamp(calendar.timegm(parsed), tz=UTC).replace(tzinfo=None)
            return min(value, now)
    return now


def _valid_image(url: str | None) -> str | None:
    if url and url.startswith(("http://", "https://")):
        return url
    return None


def extract_image(entry) -> str | None:
    """Find the best image URL in a feed entry."""
    for key in ("media_content", "media_thumbnail"):
        for media in entry.get(key) or []:
            medium = media.get("medium") or media.get("type", "image")
            if "image" in medium or key == "media_thumbnail":
                if url := _valid_image(media.get("url")):
                    return url
    for link in entry.get("links") or []:
        if link.get("rel") == "enclosure" and str(link.get("type", "")).startswith("image"):
            if url := _valid_image(link.get("href")):
                return url
    for enclosure in entry.get("enclosures") or []:
        if str(enclosure.get("type", "")).startswith("image"):
            if url := _valid_image(enclosure.get("href") or enclosure.get("url")):
                return url
    # Last resort: first <img> inside the HTML body.
    raw = ""
    if entry.get("content"):
        raw = entry["content"][0].get("value", "")
    raw = raw or entry.get("summary", "")
    if "<img" in raw:
        img = BeautifulSoup(raw, "html.parser").find("img")
        if img is not None:
            return _valid_image(img.get("src"))
    return None


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'“])", text) if s.strip()]
