"""TDD cycle 2: publishers often append their own name to headlines
("... - BBC News", "... | Reuters"). That noise lowers title similarity and
breaks story clustering, so it must be stripped."""
import pytest

from pipeline.clean import clean_title


@pytest.mark.parametrize("raw, source, expected", [
    ("Nvidia unveils new AI chip - BBC News", "BBC News", "Nvidia unveils new AI chip"),
    ("Nvidia unveils new AI chip | BBC News", "BBC News", "Nvidia unveils new AI chip"),
    ("Nvidia unveils new AI chip – bbc news", "BBC News", "Nvidia unveils new AI chip"),
    ("Nvidia unveils new AI chip — BBC", "BBC News", "Nvidia unveils new AI chip"),
])
def test_strips_trailing_source_name(raw, source, expected):
    assert clean_title(raw, source) == expected


def test_keeps_dashes_that_are_part_of_the_headline():
    assert clean_title("India vs Australia - live score", "BBC News") == "India vs Australia - live score"


def test_never_returns_empty_title():
    assert clean_title("BBC News", "BBC News") == "BBC News"


def test_decodes_html_entities_and_whitespace():
    assert clean_title("  Markets &amp; <b>shares</b>  rise ", "X") == "Markets & shares rise"
