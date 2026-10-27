"""Shared fixtures.

Tests are split into two layers:
  tests/unit/         pure functions and single classes, no database or network
  tests/integration/  real SQLite database, HTTP layer, local HTTP servers, CLI
Each test is auto-marked by folder, so you can run `pytest -m unit` or `pytest -m integration`.
"""
import http.server
import logging
import threading
from datetime import datetime
from functools import partial
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import create_app
from pipeline.enrich import LiteProcessor
from pipeline.run import run_pipeline

FIXTURES = Path(__file__).parent / "fixtures"
logging.getLogger("httpx").setLevel(logging.WARNING)  # keep test output readable
NOW = datetime(2026, 10, 24, 12, 0, 0)

FEED_FILES = {
    "https://example.com/rss": FIXTURES / "sample_feed.xml",
    "https://another.example.org/rss": FIXTURES / "second_feed.xml",
}


def pytest_collection_modifyitems(items):
    for item in items:
        layer = Path(str(item.fspath)).parent.name
        if layer in ("unit", "integration"):
            item.add_marker(getattr(pytest.mark, layer))


def fake_fetcher(url: str) -> bytes:
    if url not in FEED_FILES:
        raise ConnectionError(f"cannot reach {url}")
    return FEED_FILES[url].read_bytes()


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    database.configure(path)
    database.init_db()
    yield path
    database.get_engine().dispose()


@pytest.fixture
def run_once(db_path):
    def _run(**kwargs):
        return run_pipeline(
            feeds_path=kwargs.pop("feeds_path", FIXTURES / "feeds.json"),
            fetcher=kwargs.pop("fetcher", fake_fetcher),
            processor=kwargs.pop("processor", LiteProcessor()),
            now=kwargs.pop("now", NOW),
            **kwargs,
        )
    return _run


@pytest.fixture
def client(run_once):
    run_once()
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def http_server(tmp_path):
    """A real HTTP server on localhost serving files from a temp folder."""
    root = tmp_path / "www"
    root.mkdir()

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(root)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield root, f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
