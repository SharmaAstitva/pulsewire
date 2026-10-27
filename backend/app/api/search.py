from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.common import paginate, visible_articles
from app.database import get_db
from app.models import Article
from app.schemas import PaginatedArticles

router = APIRouter(tags=["search"])


ESCAPE = "\\"
SEARCHABLE = (Article.title, Article.summary, Article.content)


def like_pattern(term: str) -> str:
    """Match `term` literally: % and _ are SQL wildcards, so escape them."""
    for char in (ESCAPE, "%", "_"):
        term = term.replace(char, ESCAPE + char)
    return f"%{term}%"


@router.get("/search", response_model=PaginatedArticles)
def search(
    q: str = Query(..., min_length=2, max_length=100),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    category: str | None = None,
    db: Session = Depends(get_db),
):
    query = visible_articles()
    # Every word must appear in the title, summary or body.
    for term in q.split()[:6]:
        pattern = like_pattern(term)
        query = query.where(or_(*(column.ilike(pattern, escape=ESCAPE) for column in SEARCHABLE)))
    if category:
        query = query.where(Article.topic_primary == category)
    query = query.order_by(Article.trending_score.desc(), Article.id.desc())
    return paginate(db, query, page, limit)
