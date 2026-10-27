from datetime import datetime, timedelta

import pytest

from pipeline.rank import coverage_score, recency_score, trending_score

NOW = datetime(2026, 10, 24, 12)


def test_recency_halves_every_12_hours():
    assert recency_score(NOW, NOW) == pytest.approx(1.0)
    assert recency_score(NOW - timedelta(hours=12), NOW) == pytest.approx(0.5)
    assert recency_score(NOW - timedelta(hours=24), NOW) == pytest.approx(0.25)


def test_coverage_score_grows_and_caps():
    assert coverage_score(1) == 0
    assert coverage_score(2) < coverage_score(4) < coverage_score(8) == 1.0
    assert coverage_score(50) == 1.0


def test_fresh_widely_covered_story_ranks_higher():
    old_story = trending_score(NOW - timedelta(hours=20), NOW, 0.9, 0.5, 1)
    big_story = trending_score(NOW - timedelta(hours=2), NOW, 0.9, 0.5, 4)
    assert big_story > old_story
