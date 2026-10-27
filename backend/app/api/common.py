import math

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import Article
from app.schemas import ArticleOut, Meta, PaginatedArticles


def visible_articles() -> Select:
    """Articles shown to readers: not archived, and only one per story."""
    return select(Article).where(
        Article.is_archived.is_(False),
        Article.is_duplicate.is_(False),
    )


def paginate(db: Session, query: Select, page: int, limit: int) -> PaginatedArticles:
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    rows = db.scalars(query.offset((page - 1) * limit).limit(limit)).all()
    return PaginatedArticles(
        data=[ArticleOut.model_validate(row) for row in rows],
        meta=Meta(total=total, page=page, limit=limit, pages=max(1, math.ceil(total / limit))),
    )
