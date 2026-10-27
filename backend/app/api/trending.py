from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.common import visible_articles
from app.database import get_db
from app.models import Article
from app.schemas import ArticleOut

router = APIRouter(tags=["trending"])


@router.get("/trending", response_model=list[ArticleOut])
def trending(
    limit: int = Query(10, ge=1, le=20),
    category: str | None = None,
    db: Session = Depends(get_db),
):
    query = visible_articles()
    if category:
        query = query.where(Article.topic_primary == category)
    query = query.order_by(Article.trending_score.desc(), Article.id.desc()).limit(limit)
    return db.scalars(query).all()
