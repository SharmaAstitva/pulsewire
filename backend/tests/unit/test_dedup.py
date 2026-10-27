from pipeline.dedup import StoryClusterer, jaccard, title_tokens


def test_same_story_different_wording_matches():
    clusterer = StoryClusterer()
    clusterer.add("story-1", "Nvidia unveils new AI chip as tech stocks surge to record high")
    assert clusterer.match("Nvidia unveils new AI chip, tech stocks surge to record high") == "story-1"


def test_different_stories_do_not_match():
    clusterer = StoryClusterer()
    clusterer.add("story-1", "Nvidia unveils new AI chip as tech stocks surge to record high")
    assert clusterer.match("India beat Australia to win cricket World Cup final") is None


def test_very_short_titles_are_never_merged():
    clusterer = StoryClusterer()
    clusterer.add("story-1", "Live updates")
    assert clusterer.match("Live updates") is None


def test_tokens_ignore_stopwords_and_plurals():
    assert title_tokens("The strikes") == title_tokens("strike")
    assert jaccard(frozenset(), frozenset({"a"})) == 0.0
