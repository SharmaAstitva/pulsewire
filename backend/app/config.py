"""Central configuration. Everything is read from environment variables so the
same code runs locally, in GitHub Actions and on Render without edits."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Where the SQLite database lives.
DB_PATH = Path(os.getenv("PULSEWIRE_DB", BASE_DIR / "data" / "pulsewire.db"))

# If set, the API downloads the latest database snapshot from this URL
# (the `data` branch published by the pipeline workflow) and refreshes it.
DATA_URL = os.getenv("DATA_URL", "").strip()
DATA_REFRESH_MINUTES = int(os.getenv("DATA_REFRESH_MINUTES", "30"))

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))

# Pipeline settings
AI_BACKEND = os.getenv("AI_BACKEND", "lite")          # "lite" or "transformers"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()  # optional: better summaries
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
FEEDS_PATH = Path(os.getenv("FEEDS_PATH", BASE_DIR / "feeds.json"))
MAX_ITEMS_PER_FEED = int(os.getenv("MAX_ITEMS_PER_FEED", "15"))
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "7"))

# Topic labels shared by the classifier, the API and the frontend navbar.
TOPICS = [
    "World News",
    "Politics",
    "Technology",
    "Finance",
    "Science",
    "Health",
    "Sports",
    "Entertainment",
]
