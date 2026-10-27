import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import config, data_sync, rate_limit
from app.api import articles, categories, health, search, sources, trending
from app.database import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    data_sync.start()  # no-op unless DATA_URL is set
    init_db()          # makes sure tables exist even before the first pipeline run
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="PulseWire API",
        description="AI news intelligence: summaries, sentiment, topics and trending stories.",
        version="1.0.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Middleware runs in reverse order of registration, so CORS (added last)
    # wraps the rate limiter and 429 responses still carry CORS headers.
    rate_limit.install(
        app,
        rate_limit.RateLimiter(limit=config.RATE_LIMIT_PER_MINUTE, window_seconds=60),
        exempt_paths=("/api/health",),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    for module in (articles, trending, categories, search, sources):
        app.include_router(module.router, prefix="/api/v1")
    app.include_router(health.router, prefix="/api")

    @app.get("/", include_in_schema=False)
    def root(request: Request):
        return {"name": "PulseWire API", "docs": str(request.url_for("swagger_ui_html"))}

    return app


app = create_app()
