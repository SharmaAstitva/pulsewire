from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Source
from app.schemas import SourceOut

router = APIRouter(tags=["sources"])


@router.get("/sources", response_model=list[SourceOut])
def sources(db: Session = Depends(get_db)):
    return db.scalars(select(Source).order_by(Source.name)).all()
