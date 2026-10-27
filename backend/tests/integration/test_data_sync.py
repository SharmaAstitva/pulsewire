"""The API downloading database snapshots from a real HTTP server."""
import hashlib
import http.server
import threading

import pytest
from fastapi.testclient import TestClient

from app import config, data_sync, database
from app.main import create_app


class SnapshotServer:
    """Serves bytes with an ETag and answers 304 when it hasn't changed (like GitHub raw)."""

    def __init__(self):
        self.body = b""
        self.requests = 0
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                outer.requests += 1
                etag = f'"{hashlib.md5(outer.body).hexdigest()}"'
                if self.headers.get("If-None-Match") == etag:
                    self.send_response(304)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("ETag", etag)
                self.send_header("Content-Length", str(len(outer.body)))
                self.end_headers()
                self.wfile.write(outer.body)

            def log_message(self, *args):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/pulsewire.db"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()


@pytest.fixture
def snapshot_server():
    server = SnapshotServer()
    yield server
    server.server.shutdown()


@pytest.fixture
def published_db(run_once, db_path):
    """A real database produced by the pipeline, as the workflow would publish it."""
    run_once()
    database.get_engine().dispose()
    return db_path.read_bytes()


@pytest.fixture
def api_config(tmp_path, monkeypatch):
    target = tmp_path / "api" / "pulsewire.db"
    monkeypatch.setattr(config, "DB_PATH", target)
    monkeypatch.setattr(data_sync, "_state",
                        {"enabled": False, "etag": None, "last_sync": None, "last_error": None})
    return target


def test_installs_snapshot_and_api_serves_it(snapshot_server, published_db, api_config):
    snapshot_server.body = published_db

    assert data_sync.sync_once(snapshot_server.url) is True
    assert api_config.read_bytes() == published_db

    with TestClient(create_app()) as client:
        assert client.get("/api/v1/articles").json()["meta"]["total"] == 4


def test_unchanged_snapshot_is_not_downloaded_again(snapshot_server, published_db, api_config):
    snapshot_server.body = published_db
    data_sync.sync_once(snapshot_server.url)

    assert data_sync.sync_once(snapshot_server.url) is False   # server answered 304
    assert snapshot_server.requests == 2


def test_invalid_snapshot_is_rejected_and_old_data_kept(snapshot_server, published_db, api_config):
    snapshot_server.body = published_db
    data_sync.sync_once(snapshot_server.url)

    snapshot_server.body = b"<html>404: Not Found</html>"
    with pytest.raises(ValueError):
        data_sync.sync_once(snapshot_server.url)
    assert api_config.read_bytes() == published_db


def test_startup_survives_unreachable_snapshot(api_config, monkeypatch):
    monkeypatch.setattr(config, "DATA_URL", "http://127.0.0.1:9/missing.db")  # nothing listens on port 9
    monkeypatch.setattr(config, "DATA_REFRESH_MINUTES", 10_000)

    with TestClient(create_app()) as client:
        health = client.get("/api/health").json()
    assert health["status"] == "ok"            # API still starts, with an empty database
    assert health["snapshot"]["enabled"] is True
    assert health["snapshot"]["last_error"]
