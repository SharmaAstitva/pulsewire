"""A small in-memory, fixed-window rate limiter.

Replaces slowapi, whose middleware silently stopped matching routes on newer
FastAPI versions (caught by tests/integration/test_api_behaviour.py)."""
import threading
import time
from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60, clock: Callable[[], float] = time.monotonic):
        self.limit = limit
        self.window = window_seconds
        self.clock = clock
        self._windows: dict[str, tuple[float, int]] = {}  # client -> (window start, count)
        self._lock = threading.Lock()

    def __len__(self) -> int:
        return len(self._windows)

    def hit(self, client: str) -> tuple[bool, int]:
        """Record one request. Returns (allowed, seconds until the window resets)."""
        now = self.clock()
        with self._lock:
            self._evict_expired(now)
            start, count = self._windows.get(client, (now, 0))
            count += 1
            self._windows[client] = (start, count)
            retry_after = max(1, int(start + self.window - now))
            return count <= self.limit, retry_after

    def _evict_expired(self, now: float) -> None:
        expired = [c for c, (start, _) in self._windows.items() if now - start >= self.window]
        for client in expired:
            del self._windows[client]


def install(app: FastAPI, limiter: RateLimiter, exempt_paths: tuple[str, ...] = ()) -> None:
    @app.middleware("http")
    async def rate_limit(request: Request, call_next):
        if request.url.path in exempt_paths or request.method == "OPTIONS":
            return await call_next(request)
        client = request.client.host if request.client else "unknown"
        allowed, retry_after = limiter.hit(client)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": f"Too many requests. Try again in {retry_after} seconds."},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)
