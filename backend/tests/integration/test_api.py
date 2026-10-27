def test_articles_envelope_and_pagination(client):
    body = client.get("/api/v1/articles", params={"limit": 2}).json()
    assert set(body) == {"data", "meta"}
    assert body["meta"] == {"total": 4, "page": 1, "limit": 2, "pages": 2}
    scores = [a["trending_score"] for a in body["data"]]
    assert scores == sorted(scores, reverse=True)
    assert body["data"][0]["published_at"].endswith("Z")


def test_duplicates_hidden_and_filters_work(client):
    titles = [a["title"] for a in client.get("/api/v1/articles").json()["data"]]
    assert sum(t.startswith("Nvidia") for t in titles) == 1
    sports = client.get("/api/v1/articles", params={"category": "Sports"}).json()["data"]
    assert [a["topic_primary"] for a in sports] == ["Sports"]
    negative = client.get("/api/v1/articles", params={"sentiment": "negative"}).json()["data"]
    assert all(a["sentiment"] == "negative" for a in negative) and negative


def test_article_detail_lists_other_coverage(client):
    nvidia = client.get("/api/v1/search", params={"q": "nvidia"}).json()["data"][0]
    detail = client.get(f"/api/v1/articles/{nvidia['id']}").json()
    assert detail["coverage_count"] == 2
    assert [c["source"] for c in detail["also_covered_by"]] == ["Another Outlet"]
    assert detail["topic_scores"]


def test_article_not_found(client):
    assert client.get("/api/v1/articles/99999").status_code == 404


def test_trending_categories_sources(client):
    trending = client.get("/api/v1/trending", params={"limit": 3}).json()
    assert isinstance(trending, list) and len(trending) == 3
    categories = client.get("/api/v1/categories").json()
    assert sum(c["count"] for c in categories) == 4
    assert all(-1 <= c["avg_sentiment"] <= 1 for c in categories)
    assert len(client.get("/api/v1/sources").json()) == 3


def test_search_requires_all_terms(client):
    assert client.get("/api/v1/search", params={"q": "cricket australia"}).json()["meta"]["total"] == 1
    assert client.get("/api/v1/search", params={"q": "cricket nvidia"}).json()["meta"]["total"] == 0
    assert client.get("/api/v1/search", params={"q": "x"}).status_code == 422


def test_invalid_params_rejected(client):
    assert client.get("/api/v1/articles", params={"limit": 500}).status_code == 422
    assert client.get("/api/v1/articles", params={"sort": "random"}).status_code == 422


def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok" and body["articles"] == 5
    assert body["last_pipeline_run"]["new_articles"] == 5
