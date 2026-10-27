"""Pipeline orchestrator.

    python -m pipeline.run                      # uses AI_BACKEND (default: lite)
    python -m pipeline.run --ai transformers    # local HuggingFace models
"""
import argparse
import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import delete, select, update

from app import config, database
from app.models import Article, PipelineRun, Source
from pipeline.dedup import StoryClusterer
from pipeline.enrich import LiteProcessor, get_processor, scores_json
from pipeline.ingest import Fetcher, fetch_all, http_fetch, load_feeds
from pipeline.rank import rescore_all

log = logging.getLogger("pulsewire.pipeline")
CLUSTER_WINDOW_HOURS = 48


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _sync_sources(db, feeds: list[dict]) -> None:
    existing = {s.url: s for s in db.scalars(select(Source)).all()}
    for feed in feeds:
        source = existing.get(feed["url"]) or Source(url=feed["url"])
        source.name = feed["name"]
        source.category = feed.get("category")
        source.authority_score = float(feed.get("authority", 0.5))
        source.is_active = True
        db.add(source)
    db.flush()


def run_pipeline(feeds_path: Path | None = None, ai_backend: str | None = None,
                 max_items: int | None = None, fetcher: Fetcher = http_fetch,
                 processor=None, now: datetime | None = None) -> dict:
    started = time.perf_counter()
    now = now or utcnow()
    database.init_db()
    processor = processor or get_processor(ai_backend)
    fallback = LiteProcessor()
    db = database.SessionLocal()
    run = PipelineRun(started_at=now, ai_backend=processor.name)
    db.add(run)
    db.commit()

    try:
        # 1. Ingest
        feeds = load_feeds(feeds_path or config.FEEDS_PATH)
        _sync_sources(db, feeds)
        results = fetch_all(feeds, max_items or config.MAX_ITEMS_PER_FEED, fetcher)
        sources = {s.url: s for s in db.scalars(select(Source)).all()}
        for result in results:
            source = sources[result.source["url"]]
            source.last_fetched = now
            source.fetch_count += 1
            if result.error:
                source.error_count += 1
                source.last_error = result.error
            else:
                source.last_error = None
        run.feeds_ok = sum(r.error is None for r in results)
        run.feeds_failed = len(results) - run.feeds_ok
        incoming = [a for r in results for a in r.articles]
        run.fetched = len(incoming)

        # 2. Skip what we already have (exact URL match)
        known = set(db.scalars(select(Article.url_hash)).all())
        fresh, seen = [], set()
        for raw in sorted(incoming, key=lambda a: a.published_at):
            if raw.url_hash not in known and raw.url_hash not in seen:
                seen.add(raw.url_hash)
                fresh.append(raw)

        # 3. Cluster similar stories against the last 48h
        clusterer = StoryClusterer()
        window = now - timedelta(hours=CLUSTER_WINDOW_HOURS)
        for story in db.scalars(select(Article).where(
                Article.is_duplicate.is_(False), Article.published_at >= window)).all():
            clusterer.add(story, story.title)

        # 4. Enrich and store
        for i, raw in enumerate(fresh, 1):
            canonical = clusterer.match(raw.title)
            article = Article(
                url=raw.url, url_hash=raw.url_hash, title=raw.title, content=raw.content,
                image_url=raw.image_url, source=raw.source, author=raw.author,
                published_at=raw.published_at, fetched_at=now,
            )
            if canonical is not None:
                # Same story from another outlet: reuse the analysis, skip the AI cost.
                article.is_duplicate = True
                article.cluster_id = canonical.cluster_id
                for attr in ("summary", "sentiment", "sentiment_score", "topic_primary",
                             "topic_secondary", "topic_scores", "ai_backend"):
                    setattr(article, attr, getattr(canonical, attr))
                canonical.coverage_count += 1
                if not canonical.image_url and raw.image_url:
                    canonical.image_url = raw.image_url
                run.duplicates += 1
            else:
                backend_used = processor.name
                try:
                    enrichment = processor.process(raw.title, raw.content or raw.title)
                except Exception as exc:
                    # One bad article must not sink the run: fall back to rule-based analysis.
                    log.warning("Enrichment failed for %r, using lite fallback: %s", raw.title, exc)
                    enrichment = fallback.process(raw.title, raw.content or raw.title)
                    backend_used = "lite-fallback"
                    run.enrich_failures += 1
                article.summary = enrichment.summary
                article.sentiment = enrichment.sentiment
                article.sentiment_score = enrichment.sentiment_score
                article.topic_primary = enrichment.topic_primary
                article.topic_secondary = enrichment.topic_secondary
                article.topic_scores = scores_json(enrichment)
                article.ai_backend = backend_used
            db.add(article)
            db.flush()
            if canonical is None:
                article.cluster_id = article.id
                clusterer.add(article, article.title)
            run.new_articles += 1
            if i % 25 == 0:
                db.commit()
                log.info("Processed %d/%d new articles", i, len(fresh))

        # 5. Retention: archive old stories, drop very old ones to keep the snapshot small
        cutoff = now - timedelta(days=config.RETENTION_DAYS)
        run.archived = db.execute(
            update(Article)
            .where(Article.published_at < cutoff, Article.is_archived.is_(False))
            .values(is_archived=True)
        ).rowcount or 0
        purge_before = cutoff - timedelta(days=config.RETENTION_DAYS)
        db.execute(delete(Article).where(Article.published_at < purge_before))

        # 6. Rank
        rescore_all(db, now)

        run.status = "success" if run.feeds_ok else "failed"
    except Exception as exc:
        db.rollback()
        run.status = "failed"
        run.error = str(exc)[:2000]
        raise
    finally:
        run.finished_at = utcnow()
        run.duration_seconds = round(time.perf_counter() - started, 2)
        db.commit()
        summary = {
            "status": run.status, "ai_backend": run.ai_backend, "feeds_ok": run.feeds_ok,
            "feeds_failed": run.feeds_failed, "fetched": run.fetched, "new_articles": run.new_articles,
            "duplicates": run.duplicates, "archived": run.archived,
            "enrich_failures": run.enrich_failures, "duration_seconds": run.duration_seconds,
        }
        db.close()
    database.vacuum()
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PulseWire news pipeline once.")
    parser.add_argument("--ai", choices=["lite", "transformers"], default=None,
                        help="AI backend (default: AI_BACKEND env var or 'lite')")
    parser.add_argument("--feeds", type=Path, default=None, help="Path to feeds.json")
    parser.add_argument("--max-items", type=int, default=None, help="Max articles per feed")
    parser.add_argument("--db", type=Path, default=None, help="SQLite file to write to")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if args.db:
        database.configure(args.db)
    summary = run_pipeline(args.feeds, args.ai, args.max_items)
    print(json.dumps(summary, indent=2))
    if summary["status"] != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
