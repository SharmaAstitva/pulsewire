"""Integration tests written before the code (TDD cycles 1-3)."""
from sqlalchemy import select

from app import database
from app.models import Article, PipelineRun
from pipeline.enrich import LiteProcessor
from tests.conftest import FIXTURES, fake_fetcher


# ---- Cycle 1: search must treat % and _ as literal characters, not SQL wildcards
def test_search_does_not_treat_percent_as_wildcard(client):
    assert client.get("/api/v1/search", params={"q": "%%"}).json()["meta"]["total"] == 0


def test_search_does_not_treat_underscore_as_wildcard(client):
    assert client.get("/api/v1/search", params={"q": "__"}).json()["meta"]["total"] == 0


# ---- Cycle 2: source suffixes are stripped during ingestion, so clustering works
def test_story_with_source_suffix_is_clustered(run_once, tmp_path):
    suffixed = tmp_path / "suffixed.xml"
    suffixed.write_text(
        (FIXTURES / "second_feed.xml").read_text().replace(
            "Nvidia unveils new AI chip, tech stocks surge to record high",
            "Nvidia unveils new AI chip as tech stocks surge to record high - Another Outlet",
        )
    )

    def fetcher(url):
        if url == "https://another.example.org/rss":
            return suffixed.read_bytes()
        return fake_fetcher(url)

    summary = run_once(fetcher=fetcher)
    assert summary["duplicates"] == 1
    with database.SessionLocal() as db:
        titles = db.scalars(select(Article.title)).all()
    assert not any(t.endswith("Another Outlet") for t in titles)


# ---- Cycle 3: one article failing AI enrichment must not fail the whole run
class FlakyProcessor(LiteProcessor):
    name = "flaky"

    def process(self, title, text):
        if "Floods" in title:
            raise RuntimeError("model crashed")
        return super().process(title, text)


def test_enrichment_failure_falls_back_instead_of_failing_run(run_once):
    summary = run_once(processor=FlakyProcessor())

    assert summary["status"] == "success"
    assert summary["new_articles"] == 5
    with database.SessionLocal() as db:
        floods = db.scalars(select(Article).where(Article.title.like("Floods%"))).one()
        assert floods.ai_backend == "lite-fallback"
        assert floods.sentiment == "negative"
        assert db.scalars(select(PipelineRun)).one().enrich_failures == 1


# ---- Cycle 4: databases created by an older version get new columns automatically
def test_old_database_is_upgraded_in_place(tmp_path):
    import sqlite3

    old = tmp_path / "old.db"
    with sqlite3.connect(old) as conn:
        conn.execute("CREATE TABLE pipeline_runs (id INTEGER PRIMARY KEY, started_at DATETIME, "
                     "status VARCHAR(20), ai_backend VARCHAR(30))")
        conn.execute("INSERT INTO pipeline_runs (started_at, status, ai_backend) "
                     "VALUES ('2026-10-01 00:00:00', 'success', 'lite')")

    database.configure(old)
    database.init_db()

    with sqlite3.connect(old) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(pipeline_runs)")}
        assert {"enrich_failures", "duplicates", "duration_seconds"} <= columns
        assert conn.execute("SELECT COUNT(*) FROM pipeline_runs").fetchone()[0] == 1  # data kept
    database.get_engine().dispose()
