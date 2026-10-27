"""The real command-line pipeline, fetching feeds over HTTP from a local server."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app import database
from app.main import create_app
from tests.conftest import FIXTURES

BACKEND = Path(__file__).resolve().parents[2]


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "pipeline.run", *map(str, args)],
                          cwd=BACKEND, capture_output=True, text=True, timeout=120)


def write_feeds(path, base_url, names):
    path.write_text(json.dumps([
        {"name": name, "url": f"{base_url}/{name}.xml", "authority": 0.8} for name in names
    ]))


def test_cli_fetches_over_http_and_api_serves_result(http_server, tmp_path):
    root, base_url = http_server
    shutil.copy(FIXTURES / "sample_feed.xml", root / "sample.xml")
    shutil.copy(FIXTURES / "second_feed.xml", root / "second.xml")
    feeds, db = tmp_path / "feeds.json", tmp_path / "cli.db"
    write_feeds(feeds, base_url, ["sample", "second", "missing"])  # "missing" returns 404

    result = run_cli("--ai", "lite", "--feeds", feeds, "--db", db)

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["feeds_ok"] == 2 and summary["feeds_failed"] == 1
    assert summary["new_articles"] == 5 and summary["duplicates"] == 1

    database.configure(db)
    with TestClient(create_app()) as client:
        sources = {s["name"]: s for s in client.get("/api/v1/sources").json()}
        assert sources["missing"]["error_count"] == 1
        assert client.get("/api/v1/articles").json()["meta"]["total"] == 4
    database.get_engine().dispose()


def test_cli_exits_with_error_when_every_feed_fails(http_server, tmp_path):
    _, base_url = http_server
    feeds = tmp_path / "feeds.json"
    write_feeds(feeds, base_url, ["nothing-here"])

    result = run_cli("--ai", "lite", "--feeds", feeds, "--db", tmp_path / "x.db")

    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "failed"
