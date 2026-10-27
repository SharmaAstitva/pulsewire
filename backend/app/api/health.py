from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import data_sync
from app.database import get_db
from app.models import Article, PipelineRun
from app.schemas import HealthOut, PipelineRunOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health(db: Session = Depends(get_db)):
    try:
        count = db.scalar(select(func.count(Article.id)).where(Article.is_archived.is_(False))) or 0
        last_run = db.scalars(
            select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(1)
        ).first()
        database = "ok"
    except Exception as exc:  # pragma: no cover - defensive
        count, last_run, database = 0, None, f"error: {exc}"
    return HealthOut(
        status="ok" if database == "ok" else "degraded",
        database=database,
        articles=count,
        last_pipeline_run=PipelineRunOut.model_validate(last_run) if last_run else None,
        snapshot=data_sync.status(),
    )
