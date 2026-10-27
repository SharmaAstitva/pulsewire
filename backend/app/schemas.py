import json
from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, field_validator


def _as_utc(value: datetime | None) -> datetime | None:
    # SQLite stores naive UTC datetimes; mark them as UTC so the frontend
    # receives "...Z" timestamps and shows correct relative times.
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


UTCDateTime = Annotated[datetime, AfterValidator(_as_utc)]


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    title: str
    summary: str | None = None
    content: str | None = None
    image_url: str | None = None
    source: str
    author: str | None = None
    published_at: UTCDateTime
    sentiment: str | None = None
    sentiment_score: float | None = None
    topic_primary: str | None = None
    topic_secondary: str | None = None
    coverage_count: int = 1
    trending_score: float = 0.0


class CoverageItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source: str
    url: str


class ArticleDetail(ArticleOut):
    topic_scores: dict[str, float] = {}
    also_covered_by: list[CoverageItem] = []

    @field_validator("topic_scores", mode="before")
    @classmethod
    def parse_scores(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        return value or {}


class Meta(BaseModel):
    total: int
    page: int
    limit: int
    pages: int


class PaginatedArticles(BaseModel):
    data: list[ArticleOut]
    meta: Meta


class CategoryOut(BaseModel):
    name: str
    count: int
    avg_sentiment: float  # -1 (negative) to +1 (positive)


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    category: str | None = None
    authority_score: float
    is_active: bool
    last_fetched: UTCDateTime | None = None
    fetch_count: int
    error_count: int


class PipelineRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    started_at: UTCDateTime
    finished_at: UTCDateTime | None = None
    status: str
    ai_backend: str
    feeds_ok: int
    feeds_failed: int
    fetched: int
    new_articles: int
    duplicates: int
    duration_seconds: float | None = None


class HealthOut(BaseModel):
    status: str
    database: str
    articles: int
    last_pipeline_run: PipelineRunOut | None = None
    snapshot: dict
