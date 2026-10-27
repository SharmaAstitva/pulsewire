"""TDD: our own fixed-window rate limiter (slowapi silently stopped working)."""
from app.rate_limit import RateLimiter


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_allows_up_to_limit_then_blocks():
    limiter = RateLimiter(limit=3, window_seconds=60, clock=FakeClock())
    assert [limiter.hit("1.2.3.4")[0] for _ in range(4)] == [True, True, True, False]


def test_reports_seconds_until_reset():
    clock = FakeClock()
    limiter = RateLimiter(limit=1, window_seconds=60, clock=clock)
    limiter.hit("ip")
    clock.now += 15
    allowed, retry_after = limiter.hit("ip")
    assert not allowed and retry_after == 45


def test_window_resets():
    clock = FakeClock()
    limiter = RateLimiter(limit=1, window_seconds=60, clock=clock)
    limiter.hit("ip")
    clock.now += 61
    assert limiter.hit("ip")[0] is True


def test_clients_are_counted_separately():
    limiter = RateLimiter(limit=1, window_seconds=60, clock=FakeClock())
    assert limiter.hit("a")[0] and limiter.hit("b")[0]
    assert limiter.hit("a")[0] is False


def test_old_entries_are_cleaned_up():
    clock = FakeClock()
    limiter = RateLimiter(limit=5, window_seconds=60, clock=clock)
    for i in range(100):
        limiter.hit(f"ip-{i}")
    clock.now += 120
    limiter.hit("new")
    assert len(limiter) == 1
