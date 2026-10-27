from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.common import paginate, visible_articles
from app.database import get_db
from app.models import Article
from app.schemas import ArticleDetail, CoverageItem, PaginatedArticles

router = APIRouter(tags=["articles"])


@router.get("/articles", response_model=PaginatedArticles)
def list_articles(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    category: str | None = None,
    sentiment: Literal["positive", "neutral", "negative"] | None = None,
    source: str | None = None,
    sort: Literal["trending", "recent"] = "trending",
    db: Session = Depends(get_db),
):
    query = visible_articles()
    if category:
        query = query.where(Article.topic_primary == category)
    if sentiment:
        query = query.where(Article.sentiment == sentiment)
    if source:
        query = query.where(Article.source == source)
    order = Article.trending_score.desc() if sort == "trending" else Article.published_at.desc()
    query = query.order_by(order, Article.id.desc())
    return paginate(db, query, page, limit)


@router.get("/articles/{article_id}", response_model=ArticleDetail)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if article is None or article.is_archived:
        raise HTTPException(status_code=404, detail="Article not found")

    detail = ArticleDetail.model_validate(article)
    if article.cluster_id is not None:
        others = db.scalars(
            select(Article)
            .where(Article.cluster_id == article.cluster_id, Article.id != article.id)
            .order_by(Article.published_at)
        ).all()
        detail.also_covered_by = [CoverageItem.model_validate(o) for o in others]
    return detail
