from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(500), unique=True)
    category: Mapped[str | None] = mapped_column(String(100))
    authority_score: Mapped[float] = mapped_column(Float, default=0.5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_fetched: Mapped[datetime | None] = mapped_column(DateTime)
    fetch_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(1000), unique=True)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(1000))
    source: Mapped[str] = mapped_column(String(200), index=True)
    author: Mapped[str | None] = mapped_column(String(300))
    published_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime)

    sentiment: Mapped[str | None] = mapped_column(String(10), index=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float)
    topic_primary: Mapped[str | None] = mapped_column(String(50), index=True)
    topic_secondary: Mapped[str | None] = mapped_column(String(50))
    topic_scores: Mapped[str | None] = mapped_column(Text)  # JSON
    ai_backend: Mapped[str | None] = mapped_column(String(30))

    # Story clustering: articles about the same event share a cluster_id.
    cluster_id: Mapped[int | None] = mapped_column(Integer, index=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    coverage_count: Mapped[int] = mapped_column(Integer, default=1)

    trending_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class PipelineRun(Base):
    """One row per pipeline execution, for observability."""

    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="running")
    ai_backend: Mapped[str] = mapped_column(String(30))
    feeds_ok: Mapped[int] = mapped_column(Integer, default=0)
    feeds_failed: Mapped[int] = mapped_column(Integer, default=0)
    fetched: Mapped[int] = mapped_column(Integer, default=0)
    new_articles: Mapped[int] = mapped_column(Integer, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, default=0)
    archived: Mapped[int] = mapped_column(Integer, default=0)
    enrich_failures: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    error: Mapped[str | None] = mapped_column(Text)
