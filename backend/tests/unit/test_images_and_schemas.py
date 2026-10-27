from datetime import UTC, datetime

from app.api.search import like_pattern
from app.schemas import ArticleDetail
from pipeline.clean import extract_image


def test_image_from_thumbnail_enclosure_and_link():
    assert extract_image({"media_thumbnail": [{"url": "https://i/t.jpg"}]}) == "https://i/t.jpg"
    assert extract_image({"enclosures": [{"type": "image/png", "href": "https://i/e.png"}]}) == "https://i/e.png"
    assert extract_image({"links": [{"rel": "enclosure", "type": "image/jpeg",
                                     "href": "https://i/l.jpg"}]}) == "https://i/l.jpg"


def test_image_ignores_non_http_and_non_images():
    assert extract_image({"media_content": [{"url": "data:image/png;base64,xx", "medium": "image"}]}) is None
    assert extract_image({"enclosures": [{"type": "audio/mpeg", "href": "https://i/a.mp3"}]}) is None
    assert extract_image({"summary": "<p>no images</p><img alt='x'>"}) is None


def _detail(**overrides):
    base = dict(id=1, url="https://x", title="t", source="s",
                published_at=datetime(2026, 10, 24, 12), topic_scores='{"Science": 0.9}')
    return ArticleDetail.model_validate(base | overrides)


def test_naive_datetimes_are_serialised_as_utc():
    detail = _detail()
    assert detail.published_at.tzinfo == UTC
    assert detail.model_dump_json().count("2026-10-24T12:00:00Z") == 1


def test_topic_scores_json_parsing():
    assert _detail().topic_scores == {"Science": 0.9}
    assert _detail(topic_scores="not json").topic_scores == {}
    assert _detail(topic_scores=None).topic_scores == {}


def test_like_pattern_escapes_wildcards():
    assert like_pattern("50%") == "%50\\%%"
    assert like_pattern("a_b") == "%a\\_b%"
    assert like_pattern("c:\\x") == "%c:\\\\x%"
