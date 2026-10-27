from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Article
from app.schemas import CategoryOut

router = APIRouter(tags=["categories"])

SENTIMENT_VALUE = case(
    (Article.sentiment == "positive", 1.0),
    (Article.sentiment == "negative", -1.0),
    else_=0.0,
)


@router.get("/categories", response_model=list[CategoryOut])
def categories(db: Session = Depends(get_db)):
    rows = db.execute(
        select(
            Article.topic_primary,
            func.count(Article.id),
            func.avg(SENTIMENT_VALUE),
        )
        .where(
            Article.is_archived.is_(False),
            Article.is_duplicate.is_(False),
            Article.topic_primary.is_not(None),
        )
        .group_by(Article.topic_primary)
        .order_by(func.count(Article.id).desc())
    ).all()
    return [
        CategoryOut(name=name, count=count, avg_sentiment=round(avg or 0.0, 3))
        for name, count, avg in rows
    ]
