"""HTTP-level behaviour beyond the basic endpoint contract."""
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app import config, database
from app.main import create_app
from app.models import PipelineRun
from tests.conftest import NOW


def test_recent_sort_orders_by_publish_time(client):
    data = client.get("/api/v1/articles", params={"sort": "recent"}).json()["data"]
    times = [a["published_at"] for a in data]
    assert times == sorted(times, reverse=True)


def test_page_past_the_end_is_empty(client):
    body = client.get("/api/v1/articles", params={"page": 99}).json()
    assert body["data"] == [] and body["meta"]["total"] == 4


def test_archived_articles_are_hidden_everywhere(run_once):
    run_once()
    run_once(now=NOW + timedelta(days=8))  # everything is now older than retention
    with TestClient(create_app()) as client:
        assert client.get("/api/v1/articles").json()["meta"]["total"] == 0
        assert client.get("/api/v1/trending").json() == []
        assert client.get("/api/v1/articles/1").status_code == 404


def test_cors_allows_only_configured_origins(run_once, monkeypatch):
    run_once()
    monkeypatch.setattr(config, "CORS_ORIGINS", ["https://pulsewire.example"])
    with TestClient(create_app()) as client:
        allowed = client.get("/api/v1/trending", headers={"Origin": "https://pulsewire.example"})
        blocked = client.get("/api/v1/trending", headers={"Origin": "https://evil.example"})
    assert allowed.headers["access-control-allow-origin"] == "https://pulsewire.example"
    assert "access-control-allow-origin" not in blocked.headers


def test_rate_limit_returns_429(client):
    responses = [client.get("/api/v1/categories") for _ in range(125)]
    assert responses[0].status_code == 200
    assert responses[-1].status_code == 429
    assert int(responses[-1].headers["retry-after"]) > 0
    assert responses[-1].json()["detail"].startswith("Too many requests")


def test_rate_limited_response_keeps_cors_headers(run_once, monkeypatch):
    # Otherwise the browser hides the 429 and the frontend sees a vague network error.
    run_once()
    monkeypatch.setattr(config, "RATE_LIMIT_PER_MINUTE", 1)
    monkeypatch.setattr(config, "CORS_ORIGINS", ["https://pulsewire.example"])
    with TestClient(create_app()) as client:
        client.get("/api/v1/trending")
        blocked = client.get("/api/v1/trending", headers={"Origin": "https://pulsewire.example"})
    assert blocked.status_code == 429
    assert blocked.headers["access-control-allow-origin"] == "https://pulsewire.example"


def test_health_check_is_never_rate_limited(client):
    statuses = {client.get("/api/health").status_code for _ in range(130)}
    assert statuses == {200}


def test_failed_run_is_recorded(run_once, tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        run_once(feeds_path=tmp_path / "does-not-exist.json")
    with database.SessionLocal() as db:
        run = db.scalars(select(PipelineRun)).one()
    assert run.status == "failed" and "does-not-exist" in run.error
