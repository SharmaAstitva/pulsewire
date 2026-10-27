from datetime import timedelta

from sqlalchemy import select

from app import database
from app.models import Article, PipelineRun, Source
from tests.conftest import NOW


def test_full_run_ingests_dedupes_and_ranks(run_once):
    summary = run_once()

    assert summary["status"] == "success"
    assert summary["feeds_ok"] == 2 and summary["feeds_failed"] == 1  # broken feed is isolated
    assert summary["fetched"] == 5        # the too-short title is skipped
    assert summary["new_articles"] == 5
    assert summary["duplicates"] == 1     # Nvidia story from the second outlet

    with database.SessionLocal() as db:
        nvidia = db.scalars(select(Article).where(Article.is_duplicate.is_(False),
                                                  Article.title.like("Nvidia%"))).one()
        assert nvidia.coverage_count == 2
        assert nvidia.topic_primary == "Technology"
        assert nvidia.image_url == "https://example.com/img/nvidia.jpg"
        assert "appeared first" not in nvidia.content
        assert all(a.trending_score > 0 for a in db.scalars(
            select(Article).where(Article.is_duplicate.is_(False))))
        broken = db.scalars(select(Source).where(Source.name == "Broken Feed")).one()
        assert broken.error_count == 1 and broken.last_error
        assert db.scalars(select(PipelineRun)).one().status == "success"


def test_second_run_is_idempotent(run_once):
    run_once()
    second = run_once(now=NOW + timedelta(hours=1))
    assert second["new_articles"] == 0 and second["fetched"] == 5


def test_old_articles_are_archived(run_once):
    run_once()
    later = run_once(now=NOW + timedelta(days=8))
    assert later["archived"] == 5
