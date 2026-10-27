"""Stage 4: trending score.

score = 0.50 * recency      (exponential decay, 12h half-life)
      + 0.20 * authority    (per-source credibility weight from feeds.json)
      + 0.15 * topic_heat   (share of the last 24h's stories in this topic)
      + 0.15 * coverage     (how many outlets covered the same story)"""
import math
from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Article, Source

HALF_LIFE_HOURS = 12.0
WEIGHTS = {"recency": 0.50, "authority": 0.20, "topic_heat": 0.15, "coverage": 0.15}


def recency_score(published_at: datetime, now: datetime) -> float:
    age_hours = max(0.0, (now - published_at).total_seconds() / 3600)
    return math.exp(-math.log(2) * age_hours / HALF_LIFE_HOURS)


def coverage_score(coverage_count: int) -> float:
    # 1 outlet -> 0, 2 -> 0.33, 4 -> 0.67, 8+ -> 1.0
    return min(1.0, math.log2(max(1, coverage_count)) / 3)


def trending_score(published_at: datetime, now: datetime, authority: float,
                   topic_heat: float, coverage_count: int) -> float:
    score = (
        WEIGHTS["recency"] * recency_score(published_at, now)
        + WEIGHTS["authority"] * authority
        + WEIGHTS["topic_heat"] * topic_heat
        + WEIGHTS["coverage"] * coverage_score(coverage_count)
    )
    return round(score, 6)


def rescore_all(db: Session, now: datetime) -> int:
    """Recompute scores for every visible article (recency changes every run)."""
    articles = db.scalars(
        select(Article).where(Article.is_archived.is_(False), Article.is_duplicate.is_(False))
    ).all()
    authority = {s.name: s.authority_score for s in db.scalars(select(Source)).all()}

    day_ago = now - timedelta(hours=24)
    recent_topics = Counter(a.topic_primary for a in articles if a.published_at >= day_ago)
    hottest = max(recent_topics.values(), default=1)

    for article in articles:
        heat = recent_topics.get(article.topic_primary, 0) / hottest
        article.trending_score = trending_score(
            article.published_at, now, authority.get(article.source, 0.5), heat, article.coverage_count
        )
    return len(articles)
